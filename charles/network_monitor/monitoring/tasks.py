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
