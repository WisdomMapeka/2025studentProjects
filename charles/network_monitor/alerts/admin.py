from django.contrib import admin
from .models import AlertRule, Alert


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    """Admin configuration for Alert Rules"""
    list_display = (
        "name", "alert_type", "device", "severity",
        "is_active", "threshold_value", "duration",
        "send_email", "send_dashboard_alert", "created_at"
    )
    list_filter = (
        "alert_type", "severity", "is_active",
        "send_email", "send_dashboard_alert", "created_at"
    )
    search_fields = (
        "name", "device__name", "alert_type", "severity"
    )
    list_editable = ("is_active", "send_email", "send_dashboard_alert")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "alert_type", "device", "severity", "is_active")
        }),
        ("Threshold Settings", {
            "fields": ("threshold_value", "duration")
        }),
        ("Notification Options", {
            "fields": ("send_email", "send_dashboard_alert")
        }),
        ("Metadata", {
            "fields": ("created_at",),
        }),
    )


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """Admin configuration for individual Alerts"""
    list_display = (
        "rule", "device", "severity", "status",
        "metric_value", "triggered_at", "acknowledged_at", "resolved_at"
    )
    list_filter = (
        "status", "severity", "rule__alert_type",
        "rule__severity", "triggered_at", "resolved_at"
    )
    search_fields = (
        "device__name", "rule__name", "message"
    )
    readonly_fields = (
        "triggered_at", "acknowledged_at", "resolved_at"
    )
    ordering = ("-triggered_at",)
    list_per_page = 25

    fieldsets = (
        ("Alert Information", {
            "fields": ("rule", "device", "severity", "status", "message", "metric_value")
        }),
        ("Timestamps", {
            "fields": ("triggered_at", "acknowledged_at", "resolved_at")
        }),
    )
