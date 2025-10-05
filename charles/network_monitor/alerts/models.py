"""
Alert system models for notifications.
Explanation: Manages alert rules and notifications for network events.
"""

from django.db import models
from monitoring.models import NetworkDevice

class AlertRule(models.Model):
    """Rules for triggering alerts"""
    ALERT_TYPES = [
        ('device_down', 'Device Down'),
        ('high_latency', 'High Latency'),
        ('high_cpu', 'High CPU Usage'),
        ('high_memory', 'High Memory Usage'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    name = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    
    # Thresholds
    threshold_value = models.FloatField(null=True, blank=True)  # For numeric thresholds
    duration = models.IntegerField(default=300)  # How long condition must persist (seconds)
    
    # Notification settings
    send_email = models.BooleanField(default=True)
    send_dashboard_alert = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_alert_type_display()}"


class Alert(models.Model):
    """Individual alert instances"""
    ALERT_STATUS = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ]
    
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE)
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE)
    message = models.TextField()
    status = models.CharField(max_length=15, choices=ALERT_STATUS, default='active')
    severity = models.CharField(max_length=10, choices=AlertRule.SEVERITY_LEVELS)
    
    # Timing
    triggered_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Additional data
    metric_value = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"{self.device.name} - {self.message}"