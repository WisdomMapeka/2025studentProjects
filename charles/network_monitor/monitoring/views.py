"""
Views for the monitoring dashboard.
Explanation: These views handle the web interface for displaying
network status and device information.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json
from .models import NetworkDevice, DeviceStatusHistory, DeviceType
from .monitoring_core import NetworkMonitor

@login_required
def dashboard(request):
    """Main monitoring dashboard"""
    devices = NetworkDevice.objects.filter(is_active=True)
    
    # Calculate statistics
    total_devices = devices.count()
    up_devices = devices.filter(status='up').count()
    down_devices = devices.filter(status='down').count()
    warning_devices = devices.filter(status='warning').count()
    
    # Recent status history (last 24 hours)
    recent_history = DeviceStatusHistory.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).select_related('device')
    
    context = {
        'devices': devices,
        'total_devices': total_devices,
        'up_devices': up_devices,
        'down_devices': down_devices,
        'warning_devices': warning_devices,
        'recent_history': recent_history[:10],  # Last 10 entries
    }
    
    return render(request, 'monitoring/dashboard.html', context)

@login_required
def device_detail(request, device_id):
    """Detailed view for a specific device"""
    device = get_object_or_404(NetworkDevice, id=device_id)
    
    # Get status history for the last 7 days
    history = DeviceStatusHistory.objects.filter(
        device=device,
        timestamp__gte=timezone.now() - timedelta(days=7)
    ).order_by('timestamp')
    
    # Calculate uptime statistics
    total_checks = history.count()
    up_checks = history.filter(status='up').count()
    uptime_percentage = (up_checks / total_checks * 100) if total_checks > 0 else 0
    
    context = {
        'device': device,
        'history': history,
        'uptime_percentage': round(uptime_percentage, 2),
        'total_checks': total_checks,
    }
    
    return render(request, 'monitoring/device_detail.html', context)

@login_required
def api_device_status(request):
    """API endpoint for device status (used for AJAX updates)"""
    devices = NetworkDevice.objects.filter(is_active=True).values(
        'id', 'name', 'ip_address', 'status', 'last_checked', 'response_time'
    )
    
    # Convert to list for JSON serialization
    device_list = list(devices)
    
    return JsonResponse({
        'devices': device_list,
        'last_updated': timezone.now().isoformat()
    })

@login_required
def api_check_device(request, device_id):
    """API endpoint to manually check a device"""
    device = get_object_or_404(NetworkDevice, id=device_id)
    
    try:
        status, info = NetworkMonitor.check_device_status(device)
        return JsonResponse({
            'success': True,
            'status': status,
            'info': info
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })



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