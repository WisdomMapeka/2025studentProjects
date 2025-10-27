"""
Author: SNMS Development Team

Description : Database models for network monitoring.
Explanation: These models represent network devices, their status history,
and monitoring configurations.
"""

from django.db import models
from django.contrib.auth.models import User

class DeviceType(models.Model):
    """Types of network devices (Router, Switch, Server, etc.)"""
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Device Type"
        verbose_name_plural = "Device Types"


class NetworkDevice(models.Model):
    """Represents a network device to be monitored"""
    DEVICE_STATUS = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('warning', 'Warning'),
        ('unknown', 'Unknown'),
    ]
    
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    device_type = models.ForeignKey(DeviceType, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Monitoring settings
    is_active = models.BooleanField(default=True)
    monitoring_interval = models.IntegerField(default=300)  # seconds
    use_snmp = models.BooleanField(default=False)
    snmp_community = models.CharField(max_length=100, blank=True)
    
    # Current status
    status = models.CharField(max_length=10, choices=DEVICE_STATUS, default='unknown')
    last_checked = models.DateTimeField(null=True, blank=True)
    response_time = models.FloatField(null=True, blank=True)  # in milliseconds
    
    # Additional info
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"
    
    class Meta:
        verbose_name = "Network Device"
        verbose_name_plural = "Network Devices"
        ordering = ['name']


class DeviceStatusHistory(models.Model):
    """Historical record of device status changes"""
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=NetworkDevice.DEVICE_STATUS)
    response_time = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    additional_info = models.JSONField(default=dict, blank=True)  # Store ping details, SNMP data, etc.
    
    class Meta:
        verbose_name = "Device Status History"
        verbose_name_plural = "Device Status History"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'timestamp']),
        ]


class SNMPConfiguration(models.Model):
    """SNMP configuration for devices that support it"""
    device = models.OneToOneField(NetworkDevice, on_delete=models.CASCADE)
    version_choices = [
        ('1', 'SNMPv1'),
        ('2c', 'SNMPv2c'),
        ('3', 'SNMPv3'),
    ]
    version = models.CharField(max_length=3, choices=version_choices, default='2c')
    community = models.CharField(max_length=100, default='public')
    username = models.CharField(max_length=100, blank=True)  # For SNMPv3
    auth_password = models.CharField(max_length=100, blank=True)  # For SNMPv3
    priv_password = models.CharField(max_length=100, blank=True)  # For SNMPv3
    
    def __str__(self):
        return f"SNMP Config for {self.device.name}"