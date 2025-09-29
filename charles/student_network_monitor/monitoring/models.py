from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class NetworkDevice(models.Model):
    DEVICE_TYPES = [
        ('router', 'Router'),
        ('switch', 'Switch'),
        ('server', 'Server'),
        ('workstation', 'Workstation'),
        ('printer', 'Printer'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
        ('unknown', 'Unknown'),
    ]
    
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    snmp_community = models.CharField(max_length=50, blank=True, null=True)
    is_monitored = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"
    
    class Meta:
        ordering = ['name']

class DeviceStatus(models.Model):
    device = models.ForeignKey(NetworkDevice, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=NetworkDevice.STATUS_CHOICES)
    response_time = models.FloatField(null=True, blank=True)  # in milliseconds
    cpu_usage = models.FloatField(null=True, blank=True)  # percentage
    memory_usage = models.FloatField(null=True, blank=True)  # percentage
    disk_usage = models.FloatField(null=True, blank=True)  # percentage
    network_throughput = models.FloatField(null=True, blank=True)  # in Mbps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'

class NetworkScan(models.Model):
    scan_type = models.CharField(max_length=20, choices=[('ping', 'Ping'), ('snmp', 'SNMP'), ('nmap', 'NMap')])
    devices_found = models.IntegerField(default=0)
    devices_up = models.IntegerField(default=0)
    devices_down = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)  # in seconds
    
    def success_rate(self):
        if self.devices_found > 0:
            return (self.devices_up / self.devices_found) * 100
        return 0