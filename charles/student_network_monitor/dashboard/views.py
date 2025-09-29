from django.shortcuts import render

# Create your views here.
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