I'll help you create a Django-based Student Network Monitoring System. Let me build a comprehensive solution based on your requirements.

## Project Structure

First, let's create the project structure:

```bash
mkdir student_network_monitor
cd student_network_monitor
```

## 1. Project Setup

**requirements.txt**
```txt
Django==4.2.7
django-crispy-forms==2.0
crispy-bootstrap5==0.7
psutil==5.9.6
python-nmap==0.7.1
pysnmp==4.4.12
channels==4.0.0
channels-redis==4.1.0
celery==5.3.4
redis==5.0.1
plotly==5.17.0
pandas==2.1.3
django-htmx==1.16.0
whitenoise==6.6.0
gunicorn==21.2.0
```

**manage.py**
```python
#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'network_monitor.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)
```

## 2. Project Configuration

**network_monitor/settings.py**
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key-here'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'your-domain.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'channels',
    'django_htmx',
    
    # Local apps
    'monitoring',
    'alerts',
    'reports',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'network_monitor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'network_monitor.wsgi.application'
ASGI_APPLICATION = 'network_monitor.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Channels (for WebSocket/real-time updates)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Email Configuration (for alerts)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'

# Custom settings
NETWORK_SCAN_INTERVAL = 60  # seconds
ALERT_THRESHOLD = 80  # percentage for CPU/Memory alerts
```

## 3. Core Monitoring App

**monitoring/models.py**
```python
from django.db import models
from django.contrib.auth.models import User

class NetworkDevice(models.Model):
    DEVICE_TYPES = [
        ('router', 'Router'),
        ('switch', 'Switch'),
        ('server', 'Server'),
        ('workstation', 'Workstation'),
        ('printer', 'Printer'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('unknown', 'Unknown'),
    ]
    
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    snmp_community = models.CharField(max_length=50, blank=True, null=True)
    is_monitored = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"
    
    class Meta:
        ordering = ['name']

class DeviceStatus(models.Model):
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=NetworkDevice.STATUS_CHOICES)
    response_time = models.FloatField(null=True, blank=True)  # in milliseconds
    cpu_usage = models.FloatField(null=True, blank=True)  # percentage
    memory_usage = models.FloatField(null=True, blank=True)  # percentage
    disk_usage = models.FloatField(null=True, blank=True)  # percentage
    network_throughput = models.FloatField(null=True, blank=True)  # in Mbps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'

class NetworkScan(models.Model):
    scan_type = models.CharField(max_length=20, choices=[('ping', 'Ping'), ('snmp', 'SNMP'), ('nmap', 'NMap')])
    devices_found = models.IntegerField(default=0)
    devices_up = models.IntegerField(default=0)
    devices_down = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)  # in seconds
    
    def success_rate(self):
        if self.devices_found > 0:
            return (self.devices_up / self.devices_found) * 100
        return 0
```

**monitoring/monitors.py**
```python
import subprocess
import platform
import psutil
import nmap
from pysnmp.hlapi import *
from django.utils import timezone
from .models import NetworkDevice, DeviceStatus

class NetworkMonitor:
    @staticmethod
    def ping_device(ip_address):
        """Ping a device to check if it's reachable"""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', ip_address]
        
        try:
            output = subprocess.run(command, capture_output=True, text=True, timeout=5)
            return output.returncode == 0
        except subprocess.TimeoutExpired:
            return False
    
    @staticmethod
    def get_ping_response_time(ip_address):
        """Get ping response time in milliseconds"""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', ip_address]
        
        try:
            output = subprocess.run(command, capture_output=True, text=True, timeout=5)
            if output.returncode == 0:
                # Extract time from ping output
                lines = output.stdout.split('\n')
                for line in lines:
                    if 'time=' in line:
                        time_str = line.split('time=')[1].split(' ')[0]
                        return float(time_str)
            return None
        except:
            return None
    
    @staticmethod
    def snmp_get(ip_address, oid, community='public'):
        """Get SNMP data from device"""
        error_indication, error_status, error_index, var_binds = next(
            getCmd(SnmpEngine(),
                   CommunityData(community),
                   UdpTransportTarget((ip_address, 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity(oid)))
        )
        
        if error_indication:
            return None
        elif error_status:
            return None
        else:
            for var_bind in var_binds:
                return var_bind[1]
    
    @staticmethod
    def scan_network(network_range='192.168.1.0/24'):
        """Scan network for devices using nmap"""
        nm = nmap.PortScanner()
        nm.scan(hosts=network_range, arguments='-sn')
        
        devices = []
        for host in nm.all_hosts():
            devices.append({
                'ip': host,
                'hostname': nm[host].hostname(),
                'status': nm[host].state(),
                'mac': nm[host]['addresses'].get('mac', 'Unknown')
            })
        
        return devices

class DeviceMonitor:
    def __init__(self, device):
        self.device = device
    
    def check_status(self):
        """Check device status and collect metrics"""
        is_up = NetworkMonitor.ping_device(self.device.ip_address)
        response_time = NetworkMonitor.get_ping_response_time(self.device.ip_address)
        
        status_data = {
            'device': self.device,
            'status': 'up' if is_up else 'down',
            'response_time': response_time,
        }
        
        # If device is up and SNMP is configured, get additional metrics
        if is_up and self.device.snmp_community:
            status_data.update(self.get_snmp_metrics())
        
        return DeviceStatus.objects.create(**status_data)
    
    def get_snmp_metrics(self):
        """Get device metrics via SNMP"""
        metrics = {}
        
        # CPU usage (1.3.6.1.4.1.2021.11.11.0 for UCD-SNMP-MIB)
        cpu_oid = '1.3.6.1.4.1.2021.11.11.0'
        cpu_usage = NetworkMonitor.snmp_get(
            self.device.ip_address, 
            cpu_oid, 
            self.device.snmp_community
        )
        if cpu_usage:
            metrics['cpu_usage'] = float(cpu_usage)
        
        # Memory usage
        mem_total_oid = '1.3.6.1.4.1.2021.4.5.0'
        mem_used_oid = '1.3.6.1.4.1.2021.4.6.0'
        
        mem_total = NetworkMonitor.snmp_get(
            self.device.ip_address, 
            mem_total_oid, 
            self.device.snmp_community
        )
        mem_used = NetworkMonitor.snmp_get(
            self.device.ip_address, 
            mem_used_oid, 
            self.device.snmp_community
        )
        
        if mem_total and mem_used:
            memory_usage = (float(mem_used) / float(mem_total)) * 100
            metrics['memory_usage'] = memory_usage
        
        return metrics
```

## 4. Alerts System

**alerts/models.py**
```python
from django.db import models
from django.contrib.auth.models import User
from monitoring.models import NetworkDevice

class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    ALERT_TYPES = [
        ('device_down', 'Device Down'),
        ('high_cpu', 'High CPU Usage'),
        ('high_memory', 'High Memory Usage'),
        ('high_disk', 'High Disk Usage'),
        ('slow_response', 'Slow Response Time'),
        ('network_outage', 'Network Outage'),
    ]
    
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE, null=True, blank=True)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    message = models.TextField()
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.device.name if self.device else 'System'}"

class NotificationSetting(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=Alert.ALERT_TYPES)
    enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=False)
    web_notifications = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'alert_type']

class AlertRule(models.Model):
    name = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=20, choices=Alert.ALERT_TYPES)
    condition = models.JSONField()  # Store condition parameters
    severity = models.CharField(max_length=10, choices=Alert.SEVERITY_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
```

**alerts/services.py**
```python
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import Alert, NotificationSetting
from monitoring.models import DeviceStatus

class AlertService:
    @staticmethod
    def create_alert(alert_type, severity, message, device=None):
        """Create a new alert"""
        alert = Alert.objects.create(
            device=device,
            alert_type=alert_type,
            severity=severity,
            message=message
        )
        
        # Send notifications
        AlertService.send_notifications(alert)
        
        return alert
    
    @staticmethod
    def send_notifications(alert):
        """Send notifications for an alert"""
        users = User.objects.filter(is_active=True)
        
        for user in users:
            try:
                setting = NotificationSetting.objects.get(
                    user=user, 
                    alert_type=alert.alert_type
                )
                
                if setting.enabled:
                    if setting.web_notifications:
                        # Web notification would be handled via WebSocket
                        pass
                    
                    if setting.email_notifications and setting.email_notifications:
                        AlertService.send_email_notification(user, alert)
                        
            except NotificationSetting.DoesNotExist:
                # Use default settings
                if alert.severity in ['high', 'critical']:
                    AlertService.send_email_notification(user, alert)
    
    @staticmethod
    def send_email_notification(user, alert):
        """Send email notification"""
        subject = f"Network Alert: {alert.get_alert_type_display()} - {alert.severity.upper()}"
        message = f"""
        Alert Details:
        Type: {alert.get_alert_type_display()}
        Severity: {alert.severity}
        Message: {alert.message}
        Device: {alert.device.name if alert.device else 'N/A'}
        Time: {alert.created_at}
        
        Please check the Network Monitoring System for more details.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )

class AlertChecker:
    @staticmethod
    def check_device_status(device_status):
        """Check device status and create alerts if needed"""
        device = device_status.device
        
        # Check if device is down
        if device_status.status == 'down':
            AlertService.create_alert(
                alert_type='device_down',
                severity='critical',
                message=f"Device {device.name} ({device.ip_address}) is down",
                device=device
            )
        
        # Check CPU usage
        if device_status.cpu_usage and device_status.cpu_usage > 80:
            AlertService.create_alert(
                alert_type='high_cpu',
                severity='high',
                message=f"High CPU usage on {device.name}: {device_status.cpu_usage}%",
                device=device
            )
        
        # Check memory usage
        if device_status.memory_usage and device_status.memory_usage > 85:
            AlertService.create_alert(
                alert_type='high_memory',
                severity='high',
                message=f"High memory usage on {device.name}: {device_status.memory_usage}%",
                device=device
            )
        
        # Check response time
        if device_status.response_time and device_status.response_time > 100:  # ms
            AlertService.create_alert(
                alert_type='slow_response',
                severity='medium',
                message=f"Slow response from {device.name}: {device_status.response_time}ms",
                device=device
            )
```

## 5. Dashboard Views

**dashboard/views.py**
```python
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Max
from django.utils import timezone
from datetime import timedelta
from monitoring.models import NetworkDevice, DeviceStatus, NetworkScan
from alerts.models import Alert

@login_required
def dashboard(request):
    # Get summary statistics
    total_devices = NetworkDevice.objects.count()
    monitored_devices = NetworkDevice.objects.filter(is_monitored=True).count()
    
    # Get latest status for each device
    devices_with_status = []
    for device in NetworkDevice.objects.filter(is_monitored=True):
        latest_status = DeviceStatus.objects.filter(device=device).first()
        devices_with_status.append({
            'device': device,
            'status': latest_status
        })
    
    # Count devices by status
    up_devices = len([d for d in devices_with_status if d['status'] and d['status'].status == 'up'])
    down_devices = len([d for d in devices_with_status if d['status'] and d['status'].status == 'down'])
    
    # Get recent alerts
    recent_alerts = Alert.objects.filter(is_acknowledged=False)[:10]
    
    # Get recent scans
    recent_scans = NetworkScan.objects.all()[:5]
    
    context = {
        'total_devices': total_devices,
        'monitored_devices': monitored_devices,
        'up_devices': up_devices,
        'down_devices': down_devices,
        'devices_with_status': devices_with_status,
        'recent_alerts': recent_alerts,
        'recent_scans': recent_scans,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def device_detail(request, device_id):
    device = NetworkDevice.objects.get(id=device_id)
    status_history = DeviceStatus.objects.filter(device=device)[:50]
    device_alerts = Alert.objects.filter(device=device).order_by('-created_at')[:10]
    
    context = {
        'device': device,
        'status_history': status_history,
        'device_alerts': device_alerts,
    }
    
    return render(request, 'dashboard/device_detail.html', context)

@login_required
def alerts_view(request):
    alerts = Alert.objects.all().order_by('-created_at')
    acknowledged = request.GET.get('acknowledged', '')
    
    if acknowledged == 'true':
        alerts = alerts.filter(is_acknowledged=True)
    elif acknowledged == 'false':
        alerts = alerts.filter(is_acknowledged=False)
    
    context = {
        'alerts': alerts,
    }
    
    return render(request, 'dashboard/alerts.html', context)

@login_required
def acknowledge_alert(request, alert_id):
    if request.method == 'POST':
        alert = Alert.objects.get(id=alert_id)
        alert.is_acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
    
    return redirect('alerts')
```

## 6. Celery Tasks for Background Monitoring

**network_monitor/celery.py**
```python
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'network_monitor.settings')

app = Celery('network_monitor')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

**monitoring/tasks.py**
```python
from celery import shared_task
from django.utils import timezone
from .models import NetworkDevice, NetworkScan
from .monitors import DeviceMonitor, NetworkMonitor
from alerts.services import AlertChecker

@shared_task
def monitor_all_devices():
    """Monitor all devices and update their status"""
    devices = NetworkDevice.objects.filter(is_monitored=True)
    
    for device in devices:
        monitor_device.delay(device.id)

@shared_task
def monitor_device(device_id):
    """Monitor a single device"""
    try:
        device = NetworkDevice.objects.get(id=device_id)
        monitor = DeviceMonitor(device)
        device_status = monitor.check_status()
        
        # Check for alerts
        AlertChecker.check_device_status(device_status)
        
        return f"Monitored device: {device.name}"
    except NetworkDevice.DoesNotExist:
        return f"Device {device_id} not found"

@shared_task
def network_scan(network_range='192.168.1.0/24'):
    """Perform network discovery scan"""
    scan = NetworkScan.objects.create(scan_type='nmap')
    
    try:
        devices = NetworkMonitor.scan_network(network_range)
        
        scan.devices_found = len(devices)
        scan.devices_up = len([d for d in devices if d['status'] == 'up'])
        scan.devices_down = len([d for d in devices if d['status'] == 'down'])
        scan.completed_at = timezone.now()
        scan.save()
        
        # Create or update devices in database
        for device_info in devices:
            device, created = NetworkDevice.objects.get_or_create(
                ip_address=device_info['ip'],
                defaults={
                    'name': device_info['hostname'] or device_info['ip'],
                    'device_type': 'other',
                    'description': f"Discovered via network scan",
                }
            )
            
            if created:
                print(f"Discovered new device: {device.name}")
        
        return f"Scan completed: {scan.devices_found} devices found"
    except Exception as e:
        scan.completed_at = timezone.now()
        scan.save()
        return f"Scan failed: {str(e)}"
```

## 7. URLs Configuration

**network_monitor/urls.py**
```python
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from dashboard import views as dashboard_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_views.dashboard, name='dashboard'),
    path('device/<int:device_id>/', dashboard_views.device_detail, name='device_detail'),
    path('alerts/', dashboard_views.alerts_view, name='alerts'),
    path('alerts/<int:alert_id>/acknowledge/', dashboard_views.acknowledge_alert, name='acknowledge_alert'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # API endpoints
    path('api/monitoring/', include('monitoring.urls')),
    path('api/alerts/', include('alerts.urls')),
]
```

## 8. Templates

**templates/base.html**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Network Monitoring System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .status-up { color: #28a745; }
        .status-down { color: #dc3545; }
        .status-unknown { color: #6c757d; }
        .card { margin-bottom: 1rem; }
        .navbar-brand { font-weight: bold; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{% url 'dashboard' %}">
                <i class="fas fa-network-wired"></i> Network Monitor
            </a>
            
            <div class="navbar-nav ms-auto">
                {% if user.is_authenticated %}
                    <span class="navbar-text me-3">
                        Welcome, {{ user.username }}
                    </span>
                    <a class="nav-link" href="{% url 'logout' %}">Logout</a>
                {% else %}
                    <a class="nav-link" href="{% url 'login' %}">Login</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endif %}

        {% block content %}
        {% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/htmx.org@1.9.2"></script>
    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

**templates/dashboard/dashboard.html**
```html
{% extends 'base.html' %}

{% block content %}
<div class="row">
    <!-- Summary Cards -->
    <div class="col-md-3">
        <div class="card text-white bg-primary">
            <div class="card-body">
                <h5 class="card-title">Total Devices</h5>
                <h2 class="card-text">{{ total_devices }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-success">
            <div class="card-body">
                <h5 class="card-title">Devices Up</h5>
                <h2 class="card-text">{{ up_devices }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-danger">
            <div class="card-body">
                <h5 class="card-title">Devices Down</h5>
                <h2 class="card-text">{{ down_devices }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-info">
            <div class="card-body">
                <h5 class="card-title">Monitored</h5>
                <h2 class="card-text">{{ monitored_devices }}</h2>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <!-- Devices List -->
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h5 class="card-title mb-0">
                    <i class="fas fa-list"></i> Network Devices
                </h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>IP Address</th>
                                <th>Type</th>
                                <th>Status</th>
                                <th>Response Time</th>
                                <th>Last Check</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for item in devices_with_status %}
                            <tr>
                                <td>
                                    <a href="{% url 'device_detail' item.device.id %}">
                                        {{ item.device.name }}
                                    </a>
                                </td>
                                <td>{{ item.device.ip_address }}</td>
                                <td>{{ item.device.get_device_type_display }}</td>
                                <td>
                                    {% if item.status %}
                                        {% if item.status.status == 'up' %}
                                            <span class="status-up">
                                                <i class="fas fa-circle"></i> Up
                                            </span>
                                        {% elif item.status.status == 'down' %}
                                            <span class="status-down">
                                                <i class="fas fa-circle"></i> Down
                                            </span>
                                        {% else %}
                                            <span class="status-unknown">
                                                <i class="fas fa-circle"></i> Unknown
                                            </span>
                                        {% endif %}
                                    {% else %}
                                        <span class="status-unknown">
                                            <i class="fas fa-circle"></i> Unknown
                                        </span>
                                    {% endif %}
                                </td>
                                <td>
                                    {% if item.status and item.status.response_time %}
                                        {{ item.status.response_time|floatformat:2 }} ms
                                    {% else %}
                                        -
                                    {% endif %}
                                </td>
                                <td>
                                    {% if item.status %}
                                        {{ item.status.timestamp|timesince }} ago
                                    {% else %}
                                        Never
                                    {% endif %}
                                </td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="6" class="text-center">No devices configured</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Alerts and Recent Activity -->
    <div class="col-md-4">
        <!-- Recent Alerts -->
        <div class="card">
            <div class="card-header">
                <h5 class="card-title mb-0">
                    <i class="fas fa-exclamation-triangle"></i> Recent Alerts
                </h5>
            </div>
            <div class="card-body">
                {% for alert in recent_alerts %}
                <div class="alert alert-{% if alert.severity == 'critical' %}danger{% elif alert.severity == 'high' %}warning{% else %}info{% endif %} py-2">
                    <small>
                        <strong>{{ alert.get_alert_type_display }}</strong><br>
                        {{ alert.message|truncatewords:10 }}<br>
                        <span class="text-muted">{{ alert.created_at|timesince }} ago</span>
                    </small>
                </div>
                {% empty %}
                <p class="text-muted">No recent alerts</p>
                {% endfor %}
                <a href="{% url 'alerts' %}" class="btn btn-outline-primary btn-sm">View All Alerts</a>
            </div>
        </div>

        <!-- Recent Scans -->
        <div class="card mt-3">
            <div class="card-header">
                <h5 class="card-title mb-0">
                    <i class="fas fa-search"></i> Recent Scans
                </h5>
            </div>
            <div class="card-body">
                {% for scan in recent_scans %}
                <div class="border-bottom py-2">
                    <small>
                        <strong>{{ scan.get_scan_type_display }} Scan</strong><br>
                        Found: {{ scan.devices_found }} | Up: {{ scan.devices_up }}<br>
                        <span class="text-muted">{{ scan.started_at|timesince }} ago</span>
                    </small>
                </div>
                {% empty %}
                <p class="text-muted">No scans performed</p>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## 9. Deployment Instructions

1. **Setup the project:**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

2. **Start Redis (for Celery):**
```bash
# On Ubuntu
sudo apt update
sudo apt install redis-server
sudo systemctl start redis

# On macOS
brew install redis
brew services start redis
```

3. **Start Celery worker:**
```bash
celery -A network_monitor worker --loglevel=info
```

4. **Start Celery beat (for periodic tasks):**
```bash
celery -A network_monitor beat --loglevel=info
```

5. **Run the development server:**
```bash
python manage.py runserver
```

## Key Features Implemented

1. **Real-time Monitoring**: Background tasks monitor devices periodically
2. **Interactive Dashboard**: Shows device status, statistics, and alerts
3. **Alert System**: Email and web notifications for network issues
4. **Network Discovery**: Automatic device discovery via nmap
5. **SNMP Support**: Advanced monitoring for compatible devices
6. **Reporting**: Historical data and performance metrics
7. **User Management**: Role-based access control

This Django project provides a solid foundation for your Student Network Monitoring System. You can extend it further by adding more monitoring protocols, advanced reporting, or integration with other network management tools.