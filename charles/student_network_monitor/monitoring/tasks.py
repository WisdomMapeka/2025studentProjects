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