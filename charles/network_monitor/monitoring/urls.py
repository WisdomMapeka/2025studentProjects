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