from django.contrib import admin
from .models import Notification, NotificationTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "booking",
        "notification_type",
        "category",
        "subject",
        "delivered",
        "read",
        "sent_at",
    )
    list_filter = (
        "notification_type",
        "category",
        "delivered",
        "read",
        "sent_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "booking__token_number",
        "subject",
        "message",
    )
    ordering = ("-sent_at",)
    readonly_fields = ("sent_at",)

