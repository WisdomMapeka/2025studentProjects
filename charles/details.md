I'll help you build a comprehensive Django-based Student Network Monitoring System. Let's create this step by step with detailed explanations.

## Project Setup and Structure

First, let's set up the project foundation:

```bash
# Create project directory
mkdir student_network_monitor
cd student_network_monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install django
pip install django-crispy-forms
pip install crispy-bootstrap5
pip install psutil
pip install ping3
pip install pysnmp
pip install matplotlib
pip install pandas
pip install celery
pip install redis

# Start Django project
django-admin startproject network_monitor .
python manage.py startapp monitoring
python manage.py startapp alerts
python manage.py startapp reports
```

## Project Configuration

**settings.py** (excerpts):
```python
"""
Django settings for network_monitor project.
Explanation: This configuration sets up our project with necessary apps, 
database, and monitoring-specific settings.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your-secret-key-here'  # In production, use environment variables

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5',
    # Local apps
    'monitoring',
    'alerts',
    'reports',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'network_monitor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Celery Configuration (for background monitoring tasks)
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'

# Email configuration for alerts
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

## Database Models

**monitoring/models.py**:
```python
"""
Database models for network monitoring.
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
```

**alerts/models.py**:
```python
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
```

## Monitoring Core Logic

**monitoring/monitoring_core.py**:
```python
"""
Core monitoring functionality.
Explanation: This module contains the actual network monitoring logic 
using ping and SNMP protocols.
"""

import time
import subprocess
import platform
from ping3 import ping
from pysnmp.hlapi import *
import psutil
from django.utils import timezone
from .models import NetworkDevice, DeviceStatusHistory

class NetworkMonitor:
    """Core network monitoring class"""
    
    @staticmethod
    def ping_device(ip_address, timeout=5):
        """
        Ping a device to check availability
        Returns: (success, response_time_ms) or (False, None) if failed
        """
        try:
            response_time = ping(ip_address, timeout=timeout)
            if response_time is not None:
                return True, round(response_time * 1000, 2)  # Convert to milliseconds
            else:
                return False, None
        except Exception as e:
            print(f"Ping error for {ip_address}: {e}")
            return False, None
    
    @staticmethod
    def snmp_get(device, oid):
        """
        Perform SNMP GET operation
        Explanation: SNMP allows us to query detailed device information
        like CPU usage, memory, interface status, etc.
        """
        if not device.use_snmp:
            return None
            
        try:
            error_indication, error_status, error_index, var_binds = next(
                getCmd(SnmpEngine(),
                       CommunityData(device.snmp_community),
                       UdpTransportTarget((device.ip_address, 161), timeout=2.0, retries=1),
                       ContextData(),
                       ObjectType(ObjectIdentity(oid)))
            )
            
            if error_indication:
                print(f"SNMP error for {device.name}: {error_indication}")
                return None
            elif error_status:
                print(f"SNMP error status for {device.name}: {error_status}")
                return None
            else:
                for var_bind in var_binds:
                    return str(var_bind[1])
                    
        except Exception as e:
            print(f"SNMP exception for {device.name}: {e}")
            return None
    
    @staticmethod
    def get_system_uptime(device):
        """Get system uptime via SNMP"""
        # OID for system uptime
        uptime_oid = '1.3.6.1.2.1.1.3.0'
        uptime = NetworkMonitor.snmp_get(device, uptime_oid)
        return uptime
    
    @staticmethod
    def get_cpu_usage(device):
        """Get CPU usage via SNMP"""
        # This is a simplified example - actual OID depends on device type
        cpu_oid = '1.3.6.1.4.1.2021.11.11.0'  # For Linux systems
        cpu_usage = NetworkMonitor.snmp_get(device, cpu_oid)
        return cpu_usage
    
    @staticmethod
    def check_device_status(device):
        """
        Comprehensive device status check
        Explanation: This is the main method that performs all monitoring
        checks for a device and updates its status.
        """
        print(f"Checking device: {device.name} ({device.ip_address})")
        
        # Perform ping check
        is_reachable, response_time = NetworkMonitor.ping_device(device.ip_address)
        
        additional_info = {
            'response_time': response_time,
            'checked_at': timezone.now().isoformat()
        }
        
        # If device is reachable, try to get SNMP data
        if is_reachable and device.use_snmp:
            try:
                uptime = NetworkMonitor.get_system_uptime(device)
                cpu_usage = NetworkMonitor.get_cpu_usage(device)
                
                if uptime:
                    additional_info['uptime'] = uptime
                if cpu_usage:
                    additional_info['cpu_usage'] = cpu_usage
                    
            except Exception as e:
                print(f"SNMP data collection failed for {device.name}: {e}")
        
        # Determine device status based on ping result
        if is_reachable:
            status = 'up'
            # Check for high latency warning
            if response_time and response_time > 1000:  # More than 1 second
                status = 'warning'
        else:
            status = 'down'
        
        # Update device record
        device.status = status
        device.response_time = response_time
        device.last_checked = timezone.now()
        device.save()
        
        # Create status history record
        DeviceStatusHistory.objects.create(
            device=device,
            status=status,
            response_time=response_time,
            additional_info=additional_info
        )
        
        return status, additional_info
    
    @staticmethod
    def check_all_devices():
        """Check status of all active devices"""
        active_devices = NetworkDevice.objects.filter(is_active=True)
        results = []
        
        for device in active_devices:
            try:
                status, info = NetworkMonitor.check_device_status(device)
                results.append({
                    'device': device,
                    'status': status,
                    'info': info
                })
            except Exception as e:
                print(f"Error checking device {device.name}: {e}")
                results.append({
                    'device': device,
                    'status': 'unknown',
                    'info': {'error': str(e)}
                })
        
        return results
```

## Views and Dashboard

**monitoring/views.py**:
```python
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

@login_required
def device_management(request):
    """Device management interface"""
    devices = NetworkDevice.objects.all()
    device_types = DeviceType.objects.all()
    
    if request.method == 'POST':
        # Handle device creation/editing (simplified)
        pass
    
    context = {
        'devices': devices,
        'device_types': device_types,
    }
    
    return render(request, 'monitoring/device_management.html', context)
```

## URL Configuration

**network_monitor/urls.py**:
```python
"""
Main URL configuration.
Explanation: Routes URLs to appropriate views and includes app URLs.
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False)),
    path('monitoring/', include('monitoring.urls')),
    path('alerts/', include('alerts.urls')),
    path('reports/', include('reports.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]
```

**monitoring/urls.py**:
```python
"""URL configuration for monitoring app"""
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('device/<int:device_id>/', views.device_detail, name='device_detail'),
    path('device/management/', views.device_management, name='device_management'),
    path('api/device-status/', views.api_device_status, name='api_device_status'),
    path('api/check-device/<int:device_id>/', views.api_check_device, name='api_check_device'),
]
```

## Templates

**templates/base.html**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Student Network Monitoring System{% endblock %}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        .status-up { color: #28a745; }
        .status-down { color: #dc3545; }
        .status-warning { color: #ffc107; }
        .status-unknown { color: #6c757d; }
        
        .device-card { transition: transform 0.2s; }
        .device-card:hover { transform: translateY(-2px); }
        
        .stat-card { border-left: 4px solid; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{% url 'dashboard' %}">
                <i class="fas fa-network-wired"></i> Network Monitor
            </a>
            
            <div class="navbar-nav ms-auto">
                {% if user.is_authenticated %}
                    <span class="navbar-text me-3">
                        Welcome, {{ user.username }}
                    </span>
                    <a class="nav-link" href="{% url 'logout' %}">Logout</a>
                {% else %}
                    <a class="nav-link" href="{% url 'login' %}">Login</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <nav id="sidebar" class="col-md-3 col-lg-2 d-md-block bg-light sidebar collapse">
                <div class="position-sticky pt-3">
                    <ul class="nav flex-column">
                        <li class="nav-item">
                            <a class="nav-link active" href="{% url 'dashboard' %}">
                                <i class="fas fa-tachometer-alt"></i>
                                Dashboard
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'device_management' %}">
                                <i class="fas fa-server"></i>
                                Device Management
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#">
                                <i class="fas fa-bell"></i>
                                Alerts
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="#">
                                <i class="fas fa-chart-bar"></i>
                                Reports
                            </a>
                        </li>
                    </ul>
                </div>
            </nav>

            <!-- Main content -->
            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4">
                {% if messages %}
                    {% for message in messages %}
                        <div class="alert alert-{{ message.tags }} alert-dismissible fade show mt-3" role="alert">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}

                {% block content %}
                {% endblock %}
            </main>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    
    {% block extra_js %}
    {% endblock %}
</body>
</html>
```

**templates/monitoring/dashboard.html**:
```html
{% extends 'base.html' %}
{% load static %}

{% block title %}Dashboard - Network Monitor{% endblock %}

{% block content %}
<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
    <h1 class="h2">Network Dashboard</h1>
    <div class="btn-toolbar mb-2 mb-md-0">
        <button class="btn btn-sm btn-outline-secondary" onclick="refreshDashboard()">
            <i class="fas fa-sync-alt"></i> Refresh
        </button>
    </div>
</div>

<!-- Statistics Cards -->
<div class="row mb-4">
    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card stat-card border-left-primary shadow h-100 py-2">
            <div class="card-body">
                <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                            Total Devices
                        </div>
                        <div class="h5 mb-0 font-weight-bold text-gray-800">{{ total_devices }}</div>
                    </div>
                    <div class="col-auto">
                        <i class="fas fa-server fa-2x text-gray-300"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card stat-card border-left-success shadow h-100 py-2">
            <div class="card-body">
                <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
                            Devices Up
                        </div>
                        <div class="h5 mb-0 font-weight-bold text-gray-800">{{ up_devices }}</div>
                    </div>
                    <div class="col-auto">
                        <i class="fas fa-check-circle fa-2x text-gray-300"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card stat-card border-left-warning shadow h-100 py-2">
            <div class="card-body">
                <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                            Warning
                        </div>
                        <div class="h5 mb-0 font-weight-bold text-gray-800">{{ warning_devices }}</div>
                    </div>
                    <div class="col-auto">
                        <i class="fas fa-exclamation-triangle fa-2x text-gray-300"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card stat-card border-left-danger shadow h-100 py-2">
            <div class="card-body">
                <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-danger text-uppercase mb-1">
                            Devices Down
                        </div>
                        <div class="h5 mb-0 font-weight-bold text-gray-800">{{ down_devices }}</div>
                    </div>
                    <div class="col-auto">
                        <i class="fas fa-times-circle fa-2x text-gray-300"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Devices Grid -->
<div class="row">
    {% for device in devices %}
    <div class="col-xl-4 col-md-6 mb-4">
        <div class="card device-card h-100 shadow">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="m-0 font-weight-bold text-primary">{{ device.name }}</h6>
                <span class="badge bg-{% if device.status == 'up' %}success{% elif device.status == 'down' %}danger{% elif device.status == 'warning' %}warning{% else %}secondary{% endif %}">
                    {{ device.status|upper }}
                </span>
            </div>
            <div class="card-body">
                <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                            {{ device.device_type.name }}
                        </div>
                        <div class="h6 mb-0 font-weight-bold text-gray-800">
                            <i class="fas fa-network-wired"></i> {{ device.ip_address }}
                        </div>
                        {% if device.response_time %}
                        <div class="text-xs text-muted">
                            Response: {{ device.response_time }} ms
                        </div>
                        {% endif %}
                        {% if device.location %}
                        <div class="text-xs text-muted">
                            <i class="fas fa-map-marker-alt"></i> {{ device.location }}
                        </div>
                        {% endif %}
                    </div>
                    <div class="col-auto">
                        <i class="fas fa-{% if device.device_type.name == 'Router' %}router{% elif device.device_type.name == 'Switch' %}sitemap{% else %}server{% endif %} fa-2x text-gray-300"></i>
                    </div>
                </div>
            </div>
            <div class="card-footer">
                <small class="text-muted">
                    Last checked: 
                    {% if device.last_checked %}
                        {{ device.last_checked|timesince }} ago
                    {% else %}
                        Never
                    {% endif %}
                </small>
                <a href="{% url 'device_detail' device.id %}" class="btn btn-sm btn-outline-primary float-end">
                    Details
                </a>
            </div>
        </div>
    </div>
    {% empty %}
    <div class="col-12">
        <div class="alert alert-info">
            <i class="fas fa-info-circle"></i> No devices configured. 
            <a href="{% url 'device_management' %}" class="alert-link">Add some devices</a> to start monitoring.
        </div>
    </div>
    {% endfor %}
</div>

<!-- Recent Activity -->
<div class="row mt-4">
    <div class="col-12">
        <div class="card shadow">
            <div class="card-header">
                <h6 class="m-0 font-weight-bold text-primary">Recent Activity</h6>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Device</th>
                                <th>Status</th>
                                <th>Response Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for history in recent_history %}
                            <tr>
                                <td>{{ history.timestamp|timesince }} ago</td>
                                <td>{{ history.device.name }}</td>
                                <td>
                                    <span class="badge bg-{% if history.status == 'up' %}success{% elif history.status == 'down' %}danger{% elif history.status == 'warning' %}warning{% else %}secondary{% endif %}">
                                        {{ history.status|upper }}
                                    </span>
                                </td>
                                <td>
                                    {% if history.response_time %}
                                        {{ history.response_time }} ms
                                    {% else %}
                                        -
                                    {% endif %}
                                </td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="4" class="text-center">No activity recorded yet.</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
function refreshDashboard() {
    // Simple page reload for now - could be enhanced with AJAX
    location.reload();
}

// Auto-refresh every 60 seconds
setTimeout(refreshDashboard, 60000);
</script>
{% endblock %}
```

## Management Commands

**monitoring/management/commands/monitor_devices.py**:
```python
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
```

## Alert System

**alerts/alert_manager.py**:
```python
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
```

## Running the Application

**Setup Script**:
```bash
#!/bin/bash
# setup.sh

echo "Setting up Student Network Monitoring System..."

# Create migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
echo "Creating superuser account..."
python manage.py createsuperuser

# Load initial data
python manage.py loaddata device_types

echo "Setup complete!"
echo "Run 'python manage.py runserver' to start the development server."
```

## Key Features Explained:

1. **Real-time Monitoring**: Uses ping and SNMP to check device status
2. **Interactive Dashboard**: Bootstrap-based responsive interface
3. **Alert System**: Configurable rules with email notifications
4. **Historical Data**: Tracks device status over time
5. **RESTful API**: JSON endpoints for integration
6. **Modular Design**: Separate apps for monitoring, alerts, and reports

## Next Steps:

1. Run migrations and create superuser
2. Add sample devices through the admin interface
3. Configure alert rules
4. Set up cron jobs for automatic monitoring
5. Add more advanced features like network maps, performance graphs, etc.

This provides a solid foundation for a student network monitoring system that's both educational and practical!