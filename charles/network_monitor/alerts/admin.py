from django.contrib import admin
from .models import AlertRule, Alert

@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "alert_type", "severity", "device", "is_active", "threshold_value", "duration", "created_at")
    list_filter = ("alert_type", "severity", "is_active")
    search_fields = ("name", "device__name")

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("device", "severity", "status", "triggered_at", "metric_value", "message")
    list_filter = ("status", "severity", "triggered_at")
    search_fields = ("device__name", "message")
    actions = ["acknowledge", "resolve"]

    @admin.action(description="Acknowledge")
    def acknowledge(self, request, queryset):
        queryset.update(status="acknowledged")

    @admin.action(description="Resolve")
    def resolve(self, request, queryset):
        queryset.update(status="resolved")