Awesome — let’s take this from “solid foundation” to a usable system. Below I’m adding the missing pieces: **Celery integration (scheduled monitoring), Admin UX, Device CRUD with crispy-forms, Alerts UI + actions, simple Reports, fixtures, and a few settings fixes.** Drop these files in as-is.

---

# 1) Settings additions (time zone, email defaults, Celery beat)

**network_monitor/settings.py** (append/adjust)

```python
# --- Localisation ---
TIME_ZONE = "Africa/Harare"
USE_TZ = True

# --- Email defaults used by AlertManager ---
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
ADMIN_EMAIL = "alerts@example.com"  # change to your admin/team email list

# --- Static ---
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

# --- Celery/Beat schedule ---
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 60

from datetime import timedelta
CELERY_BEAT_SCHEDULE = {
    # Every minute, decide which devices are “due” based on their per-device interval
    "monitoring-tick": {
        "task": "monitoring.tasks.tick_monitoring",
        "schedule": timedelta(minutes=1),
    },
}
```

---

# 2) Celery bootstrap + periodic task

**network_monitor/celery.py**

```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "network_monitor.settings")

app = Celery("network_monitor")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

**network_monitor/**init**.py**

```python
from .celery import app as celery_app
__all__ = ("celery_app",)
```

**monitoring/tasks.py**

```python
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import NetworkDevice
from .monitoring_core import NetworkMonitor
from alerts.alert_manager import AlertManager

@shared_task
def check_device_task(device_id: int):
    device = NetworkDevice.objects.filter(id=device_id, is_active=True).first()
    if not device:
        return "Device not found or inactive"
    status, info = NetworkMonitor.check_device_status(device)
    AlertManager().check_device_alerts(device, status, info)
    return {"device": device.name, "status": status, "info": info}

@shared_task
def tick_monitoring():
    """
    Runs every minute. Only checks devices whose last_checked is older than their
    per-device `monitoring_interval` (or never checked).
    """
    now = timezone.now()
    due = []
    for d in NetworkDevice.objects.filter(is_active=True):
        if not d.last_checked or (now - d.last_checked) >= timedelta(seconds=d.monitoring_interval):
            due.append(d.id)
    for did in due:
        check_device_task.delay(did)
    return {"queued": len(due)}
```

---

# 3) Safer ping fallback + SNMP v1/2c/3 support

**monitoring/monitoring_core.py** (replace your class with this improved one)

```python
import platform, subprocess
from ping3 import ping as ping3_ping
from pysnmp.hlapi import *
from django.utils import timezone
from .models import NetworkDevice, DeviceStatusHistory, SNMPConfiguration

class NetworkMonitor:
    @staticmethod
    def ping_device(ip_address, timeout=5):
        """
        Try ping3; if raw-socket permission fails, fall back to OS ping.
        Returns: (True, ms) or (False, None)
        """
        try:
            rt = ping3_ping(ip_address, timeout=timeout)
            if rt is not None:
                return True, round(rt * 1000, 2)
        except Exception:
            pass  # fall back

        try:
            # Cross-platform OS ping
            count_flag = "-n" if platform.system().lower().startswith("win") else "-c"
            t_flag = "-w" if platform.system().lower().startswith("win") else "-W"
            cmd = ["ping", count_flag, "1", t_flag, str(timeout), ip_address]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 2)
            success = proc.returncode == 0
            # We won’t parse ms precisely (varies by locale). Just mark reachable.
            return (True, None) if success else (False, None)
        except Exception:
            return False, None

    @staticmethod
    def _snmp_params(device):
        """Build pysnmp credentials from SNMPConfiguration (if present)."""
        if not device.use_snmp:
            return None

        try:
            cfg = SNMPConfiguration.objects.get(device=device)
        except SNMPConfiguration.DoesNotExist:
            return None

        target = UdpTransportTarget((device.ip_address, 161), timeout=2.0, retries=1)
        ctx = ContextData()

        if cfg.version in ("1", "2c"):
            auth = CommunityData(cfg.community or device.snmp_community or "public", mpModel=0 if cfg.version == "1" else 1)
            return auth, target, ctx

        # SNMPv3 (noAuthNoPriv / authNoPriv / authPriv minimal support)
        if cfg.version == "3":
            # basic noAuthNoPriv if passwords are blank
            if not cfg.auth_password and not cfg.priv_password:
                auth = UsmUserData(cfg.username or "usr-none")
            elif cfg.auth_password and not cfg.priv_password:
                auth = UsmUserData(cfg.username or "usr-auth",
                                   authKey=cfg.auth_password, authProtocol=usmHMACSHAAuthProtocol)
            else:
                auth = UsmUserData(cfg.username or "usr-priv",
                                   authKey=cfg.auth_password, authProtocol=usmHMACSHAAuthProtocol,
                                   privKey=cfg.priv_password, privProtocol=usmAesCfb128Protocol)
            return auth, target, ctx

        return None

    @staticmethod
    def snmp_get(device, oid):
        params = NetworkMonitor._snmp_params(device)
        if not params:
            return None
        auth, target, ctx = params
        try:
            ei, es, ei_idx, vbs = next(getCmd(SnmpEngine(), auth, target, ctx, ObjectType(ObjectIdentity(oid))))
            if ei or es:
                return None
            for vb in vbs:
                return str(vb[1])
        except Exception:
            return None

    @staticmethod
    def get_system_uptime(device):
        return NetworkMonitor.snmp_get(device, "1.3.6.1.2.1.1.3.0")

    @staticmethod
    def get_cpu_usage(device):
        # NOTE: OIDs vary per vendor. This is a sample (UCD-SNMP-MIB on many Linux hosts)
        return NetworkMonitor.snmp_get(device, "1.3.6.1.4.1.2021.11.11.0")

    @staticmethod
    def check_device_status(device):
        is_reachable, response_time = NetworkMonitor.ping_device(device.ip_address)
        additional_info = {"response_time": response_time, "checked_at": timezone.now().isoformat()}

        if is_reachable and device.use_snmp:
            uptime = NetworkMonitor.get_system_uptime(device)
            cpu = NetworkMonitor.get_cpu_usage(device)
            if uptime: additional_info["uptime"] = uptime
            if cpu:    additional_info["cpu_usage"] = cpu

        status = "up" if is_reachable else "down"
        if is_reachable and response_time and response_time > 1000:
            status = "warning"

        device.status = status
        device.response_time = response_time
        device.last_checked = timezone.now()
        device.save(update_fields=["status", "response_time", "last_checked", "updated_at"])

        DeviceStatusHistory.objects.create(
            device=device, status=status, response_time=response_time, additional_info=additional_info
        )
        return status, additional_info

    @staticmethod
    def check_all_devices():
        results = []
        for d in NetworkDevice.objects.filter(is_active=True):
            try:
                status, info = NetworkMonitor.check_device_status(d)
                results.append({"device": d, "status": status, "info": info})
            except Exception as e:
                results.append({"device": d, "status": "unknown", "info": {"error": str(e)}})
        return results
```

---

# 4) Admin: quick triage & actions

**monitoring/admin.py**

```python
from django.contrib import admin
from .models import DeviceType, NetworkDevice, DeviceStatusHistory
from monitoring.tasks import check_device_task

@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)

@admin.register(NetworkDevice)
class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "ip_address", "device_type", "status", "is_active", "last_checked", "response_time")
    list_filter = ("device_type", "status", "is_active", "use_snmp")
    search_fields = ("name", "ip_address", "location", "description")
    actions = ["action_check_now", "action_activate", "action_deactivate"]

    @admin.action(description="Check selected devices now (async)")
    def action_check_now(self, request, queryset):
        for d in queryset:
            check_device_task.delay(d.id)

    @admin.action(description="Activate monitoring")
    def action_activate(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate monitoring")
    def action_deactivate(self, request, queryset):
        queryset.update(is_active=False)

@admin.register(DeviceStatusHistory)
class DeviceStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("device", "status", "response_time", "timestamp")
    list_filter = ("status", "timestamp")
    search_fields = ("device__name", "device__ip_address")
    date_hierarchy = "timestamp"
```

**alerts/admin.py**

```python
from django.contrib import admin
from .models import AlertRule, Alert

@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "alert_type", "severity", "device", "is_active", "threshold_value", "duration", "created_at")
    list_filter = ("alert_type", "severity", "is_active")
    search_fields = ("name", "device__name")

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("device", "severity", "status", "triggered_at", "metric_value", "message")
    list_filter = ("status", "severity", "triggered_at")
    search_fields = ("device__name", "message")
    actions = ["acknowledge", "resolve"]

    @admin.action(description="Acknowledge")
    def acknowledge(self, request, queryset):
        queryset.update(status="acknowledged")

    @admin.action(description="Resolve")
    def resolve(self, request, queryset):
        queryset.update(status="resolved")
```

---

# 5) Device create/edit (crispy-forms) + page

**monitoring/forms.py**

```python
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Fieldset
from .models import NetworkDevice

class NetworkDeviceForm(forms.ModelForm):
    class Meta:
        model = NetworkDevice
        fields = [
            "name","ip_address","mac_address","device_type","description","location",
            "is_active","monitoring_interval","use_snmp","snmp_community",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Fieldset("Identity",
                Row(Column("name", css_class="col-md-6"), Column("device_type", css_class="col-md-6")),
                Row(Column("ip_address", css_class="col-md-6"), Column("mac_address", css_class="col-md-6")),
                Row(Column("location", css_class="col-md-6"), Column("description", css_class="col-md-6")),
            ),
            Fieldset("Monitoring",
                Row(Column("is_active", css_class="col-md-3"), Column("monitoring_interval", css_class="col-md-3")),
                Row(Column("use_snmp", css_class="col-md-3"), Column("snmp_community", css_class="col-md-6")),
            ),
            Submit("save", "Save"),
        )

    def clean(self):
        data = super().clean()
        if data.get("use_snmp") and not data.get("snmp_community"):
            self.add_error("snmp_community", "Required when SNMP is enabled.")
        return data
```

**monitoring/views.py** (replace `device_management` with this CRUD-capable version)

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .forms import NetworkDeviceForm

@login_required
def device_management(request):
    """Create/update devices on one page (simple CRUD)."""
    editing_id = request.GET.get("edit")
    instance = None
    if editing_id:
        instance = get_object_or_404(NetworkDevice, id=editing_id)

    if request.method == "POST":
        if request.POST.get("delete_id"):
            obj = get_object_or_404(NetworkDevice, id=request.POST["delete_id"])
            obj.delete()
            messages.success(request, f"Deleted {obj.name}.")
            return redirect("device_management")

        form = NetworkDeviceForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"Saved {obj.name}.")
            return redirect("device_management")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = NetworkDeviceForm(instance=instance)

    devices = NetworkDevice.objects.all().select_related("device_type")
    return render(request, "monitoring/device_management.html", {"form": form, "devices": devices, "editing": instance})
```

**templates/monitoring/device_management.html**

```html
{% extends "base.html" %}
{% block title %}Device Management{% endblock %}
{% block content %}
<div class="pt-3 pb-2 mb-3 border-bottom d-flex align-items-center justify-content-between">
  <h1 class="h2">Device Management</h1>
  {% if editing %}
    <a class="btn btn-sm btn-outline-secondary" href="{% url 'device_management' %}">+ New Device</a>
  {% endif %}
</div>

<div class="row">
  <div class="col-lg-5">
    <div class="card shadow mb-4">
      <div class="card-header"><strong>{% if editing %}Edit{% else %}Add{% endif %} Device</strong></div>
      <div class="card-body">
        <form method="post">
          {% csrf_token %}
          {{ form|crispy }}
        </form>
      </div>
    </div>
  </div>
  <div class="col-lg-7">
    <div class="card shadow">
      <div class="card-header"><strong>Devices</strong></div>
      <div class="card-body table-responsive">
        <table class="table table-sm align-middle">
          <thead>
            <tr><th>Name</th><th>IP</th><th>Type</th><th>Status</th><th>Interval</th><th></th></tr>
          </thead>
          <tbody>
            {% for d in devices %}
            <tr>
              <td>{{ d.name }}</td>
              <td>{{ d.ip_address }}</td>
              <td>{{ d.device_type.name }}</td>
              <td>
                <span class="badge bg-{% if d.status == 'up' %}success{% elif d.status == 'down' %}danger{% elif d.status == 'warning' %}warning{% else %}secondary{% endif %}">
                  {{ d.status|upper }}
                </span>
              </td>
              <td>{{ d.monitoring_interval }}s</td>
              <td class="text-end">
                <a href="{% url 'device_management' %}?edit={{ d.id }}" class="btn btn-sm btn-outline-primary">Edit</a>
                <form method="post" class="d-inline" onsubmit="return confirm('Delete {{ d.name }}?');">
                  {% csrf_token %}
                  <input type="hidden" name="delete_id" value="{{ d.id }}">
                  <button class="btn btn-sm btn-outline-danger">Delete</button>
                </form>
                <a href="{% url 'device_detail' d.id %}" class="btn btn-sm btn-outline-secondary">Details</a>
              </td>
            </tr>
            {% empty %}
            <tr><td colspan="6" class="text-center">No devices yet.</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

---

# 6) Alerts UI (list, acknowledge, resolve)

**alerts/urls.py**

```python
from django.urls import path
from . import views

urlpatterns = [
    path("", views.alert_list, name="alerts_list"),
    path("<int:alert_id>/ack/", views.alert_ack, name="alert_ack"),
    path("<int:alert_id>/resolve/", views.alert_resolve, name="alert_resolve"),
]
```

**alerts/views.py**

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Alert

@login_required
def alert_list(request):
    alerts = Alert.objects.select_related("device", "rule").all()
    return render(request, "alerts/alerts_list.html", {"alerts": alerts})

@login_required
def alert_ack(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id)
    alert.status = "acknowledged"
    alert.save(update_fields=["status"])
    messages.success(request, f"Acknowledged alert for {alert.device.name}.")
    return redirect("alerts_list")

@login_required
def alert_resolve(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id)
    alert.status = "resolved"
    alert.save(update_fields=["status"])
    messages.success(request, f"Resolved alert for {alert.device.name}.")
    return redirect("alerts_list")
```

**templates/alerts/alerts_list.html**

```html
{% extends "base.html" %}
{% block title %}Alerts{% endblock %}
{% block content %}
<div class="pt-3 pb-2 mb-3 border-bottom d-flex align-items-center justify-content-between">
  <h1 class="h2">Alerts</h1>
</div>

<div class="card shadow">
  <div class="card-body table-responsive">
    <table class="table table-sm align-middle">
      <thead>
      <tr>
        <th>Time</th><th>Device</th><th>Severity</th><th>Status</th><th>Message</th><th>Metric</th><th></th>
      </tr>
      </thead>
      <tbody>
      {% for a in alerts %}
      <tr>
        <td>{{ a.triggered_at }}</td>
        <td>{{ a.device.name }}</td>
        <td><span class="badge bg-{% if a.severity == 'critical' %}danger{% elif a.severity == 'high' %}warning{% elif a.severity == 'medium' %}info{% else %}secondary{% endif %}">
          {{ a.severity|upper }}
        </span></td>
        <td>{{ a.status }}</td>
        <td>{{ a.message }}</td>
        <td>{% if a.metric_value %}{{ a.metric_value }}{% else %}-{% endif %}</td>
        <td class="text-end">
          <a class="btn btn-sm btn-outline-secondary" href="{% url 'alert_ack' a.id %}">Acknowledge</a>
          <a class="btn btn-sm btn-outline-success" href="{% url 'alert_resolve' a.id %}">Resolve</a>
        </td>
      </tr>
      {% empty %}
      <tr><td colspan="7" class="text-center">No alerts.</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
```

Add a link to Alerts in your **base.html** sidebar (you already have a placeholder). Change its `href` to `{% url 'alerts_list' %}`.

And include the app URLs in **network_monitor/urls.py** (you already `include('alerts.urls')`, good).

---

# 7) Simple Reports (CSV uptime by device for last 24h)

**reports/urls.py**

```python
from django.urls import path
from . import views

urlpatterns = [
    path("uptime/csv/", views.uptime_csv, name="uptime_csv"),
]
```

**reports/views.py**

```python
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from monitoring.models import NetworkDevice, DeviceStatusHistory
import csv

def uptime_csv(request):
    """
    Export per-device uptime percentage for the last 24 hours.
    """
    start = timezone.now() - timedelta(hours=24)
    rows = []
    for d in NetworkDevice.objects.all():
        hist = DeviceStatusHistory.objects.filter(device=d, timestamp__gte=start)
        total = hist.count()
        up = hist.filter(status="up").count()
        pct = round((up / total * 100), 2) if total else 0.00
        rows.append((d.name, d.ip_address, pct, total))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="uptime_last_24h.csv"'
    writer = csv.writer(response)
    writer.writerow(["Device", "IP", "Uptime % (24h)", "Samples"])
    writer.writerows(rows)
    return response
```

Add a Reports link in the sidebar to `{% url 'uptime_csv' %}`.

---

# 8) Fixtures (device types)

Create **monitoring/fixtures/device_types.json**

```json
[
  {"model": "monitoring.devicetype", "pk": 1, "fields": {"name": "Router", "description": "Gateway/edge router"}},
  {"model": "monitoring.devicetype", "pk": 2, "fields": {"name": "Switch", "description": "Layer 2/3 switch"}},
  {"model": "monitoring.devicetype", "pk": 3, "fields": {"name": "Server", "description": "Application or file server"}},
  {"model": "monitoring.devicetype", "pk": 4, "fields": {"name": "Access Point", "description": "Wireless AP"}}
]
```

Then:

```bash
python manage.py loaddata device_types
```

---

# 9) Quick runbook

```bash
# 1) Migrate & create superuser
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# 2) Redis (Linux)
# sudo apt-get install redis-server
# sudo systemctl enable --now redis

# 3) Start Celery worker + beat (use 2 terminals)
celery -A network_monitor worker -l info
celery -A network_monitor beat -l info

# 4) Run server
python manage.py runserver
```

**Windows tips**

* If Redis isn’t installed natively, easiest is WSL or Docker (`docker run -p 6379:6379 redis`).
* If ping3 has permission issues, our fallback to OS `ping` keeps availability checks working.

---

# 10) What you can do right now

1. Add a couple of devices in **Device Management** (tick “Use SNMP” and set community if you have an SNMP-enabled target).
2. Create **Alert Rules** in admin (e.g., type=High Latency, threshold=300 ms).
3. Watch the **Dashboard** update (auto every minute by Celery tick); or force checks via **admin action** “Check selected devices now”.

If you want, next I can add:

* **WebSocket live tiles** (Django Channels) for instant status changes,
* **Vendor-specific SNMP OIDs** (Cisco/Juniper/Mikrotik/Linux templates),
* **Role-based permissions** (students vs admins),
* **Per-device graphs** (tiny sparkline PNGs on device cards).
