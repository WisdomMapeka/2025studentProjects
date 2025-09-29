from django.db import models

# Create your models here.
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