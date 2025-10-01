from django.contrib import admin
from .models import Booking, TimeSlot


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "token_number",
        "citizen",
        "service",
        "branch",
        "booking_date",
        "booking_time",
        "status",
        "priority",
        "estimated_wait_time",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "priority", "branch", "service", "booking_date")
    search_fields = (
        "token_number",
        "citizen__username",
        "citizen__email",
        "service__name",
        "branch__name",
    )
    ordering = ("booking_date", "booking_time")
    readonly_fields = ("created_at", "updated_at")


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = (
        "branch",
        "service",
        "date",
        "start_time",
        "end_time",
        "max_capacity",
        "booked_count",
        "available",
    )
    list_filter = ("branch", "service", "date", "available")
    search_fields = ("branch__name", "service__name", "date")
    ordering = ("date", "start_time")
