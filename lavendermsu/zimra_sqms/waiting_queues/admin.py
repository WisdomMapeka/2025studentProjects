from django.contrib import admin
from .models import WaitingQueue, WaitingQueueMetrics


@admin.register(WaitingQueue)
class WaitingQueueAdmin(admin.ModelAdmin):
    list_display = (
        "queue_number",
        "booking",
        "counter",
        "status",
        "called_time",
        "serving_start_time",
        "serving_end_time",
        "wait_duration",
        "service_duration",
        "created_at",
    )
    list_filter = ("status", "counter", "created_at")
    search_fields = (
        "booking__token_number",
        "queue_number",
        "counter__name",
        "status",
    )
    ordering = ("queue_number",)
    readonly_fields = (
        "created_at",
        "called_time",
        "serving_start_time",
        "serving_end_time",
    )


@admin.register(WaitingQueueMetrics)
class WaitingQueueMetricsAdmin(admin.ModelAdmin):
    list_display = (
        "branch",
        "service",
        "date",
        "total_bookings",
        "completed_bookings",
        "average_wait_time",
        "average_service_time",
        "peak_hour",
        "created_at",
    )
    list_filter = ("branch", "service", "date")
    search_fields = ("branch__name", "service__name", "date")
    ordering = ("-date", "branch", "service")
    readonly_fields = ("created_at",)
