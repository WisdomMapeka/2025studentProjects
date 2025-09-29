"""
URL configuration for student_network_monitor project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from dashboard import views as dashboard_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_views.dashboard, name='dashboard'),
    path('device/<int:device_id>/', dashboard_views.device_detail, name='device_detail'),
    path('alerts/', dashboard_views.alerts_view, name='alerts'),
    path('alerts/<int:alert_id>/acknowledge/', dashboard_views.acknowledge_alert, name='acknowledge_alert'),
    
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # API endpoints
    path('api/monitoring/', include('monitoring.urls')),
    path('api/alerts/', include('alerts.urls')),
]