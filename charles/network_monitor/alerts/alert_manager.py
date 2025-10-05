"""
Alert management system.
Explanation: Handles alert rules and notifications when network issues are detected.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Alert, AlertRule

class AlertManager:
    """Manages alert rules and notifications"""
    
    def check_device_alerts(self, device, status, monitoring_info):
        """Check if any alerts should be triggered for this device"""
        alert_rules = AlertRule.objects.filter(
            device=device,
            is_active=True
        )
        
        for rule in alert_rules:
            if self._should_trigger_alert(rule, status, monitoring_info):
                self._trigger_alert(rule, device, monitoring_info)
    
    def _should_trigger_alert(self, rule, status, monitoring_info):
        """Determine if an alert rule should be triggered"""
        if rule.alert_type == 'device_down' and status == 'down':
            return True
        elif rule.alert_type == 'high_latency':
            response_time = monitoring_info.get('response_time')
            if response_time and response_time > rule.threshold_value:
                return True
        # Add more alert type checks as needed
        
        return False
    
    def _trigger_alert(self, rule, device, monitoring_info):
        """Create and send an alert"""
        message = self._generate_alert_message(rule, device, monitoring_info)
        
        # Create alert record
        alert = Alert.objects.create(
            rule=rule,
            device=device,
            message=message,
            severity=rule.severity,
            metric_value=monitoring_info.get('response_time')
        )
        
        # Send notifications
        if rule.send_email:
            self._send_email_alert(alert, message)
        
        if rule.send_dashboard_alert:
            # This would typically use WebSockets or similar for real-time notifications
            pass
    
    def _generate_alert_message(self, rule, device, monitoring_info):
        """Generate human-readable alert message"""
        if rule.alert_type == 'device_down':
            return f"Device {device.name} ({device.ip_address}) is DOWN"
        elif rule.alert_type == 'high_latency':
            response_time = monitoring_info.get('response_time')
            return f"High latency on {device.name}: {response_time}ms (threshold: {rule.threshold_value}ms)"
        
        return f"Alert triggered for {device.name}: {rule.alert_type}"
    
    def _send_email_alert(self, alert, message):
        """Send email notification"""
        try:
            subject = f"[{alert.severity.upper()}] Network Alert: {alert.device.name}"
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],  # Should be configurable
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send email alert: {e}")