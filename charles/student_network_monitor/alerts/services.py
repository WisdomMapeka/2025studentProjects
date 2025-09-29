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