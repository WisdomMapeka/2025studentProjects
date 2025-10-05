"""
Management command for monitoring devices.
Explanation: This command can be run manually or scheduled via cron
to perform regular device monitoring.
"""

from django.core.management.base import BaseCommand
from monitoring.models import NetworkDevice
from monitoring.monitoring_core import NetworkMonitor
from alerts.alert_manager import AlertManager

class Command(BaseCommand):
    help = 'Check status of all network devices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=int,
            help='Check only specific device',
        )

    def handle(self, *args, **options):
        device_id = options.get('device_id')
        
        if device_id:
            devices = NetworkDevice.objects.filter(id=device_id, is_active=True)
        else:
            devices = NetworkDevice.objects.filter(is_active=True)
        
        self.stdout.write(f"Checking {devices.count()} devices...")
        
        alert_manager = AlertManager()
        
        for device in devices:
            self.stdout.write(f"Checking {device.name} ({device.ip_address})...", ending=' ')
            
            try:
                status, info = NetworkMonitor.check_device_status(device)
                
                # Check for alerts
                alert_manager.check_device_alerts(device, status, info)
                
                self.stdout.write(self.style.SUCCESS(f"{status.upper()}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"ERROR: {e}"))
        
        self.stdout.write(self.style.SUCCESS("Device monitoring completed!"))