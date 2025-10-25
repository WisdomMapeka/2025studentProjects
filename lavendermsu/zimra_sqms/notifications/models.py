from django.db import models
from core.models import User
from bookings.models import Booking

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    )
    
    NOTIFICATION_CATEGORIES = (
        ('booking_confirmation', 'Booking Confirmation'),
        ('serving', 'serving'),
        ('reminder', 'Reminder'),
        ('queue_update', 'Queue Update'),
        ('service_completion', 'Service Completion'),
        ('system', 'System Notification'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, blank=True, null=True)
    category = models.CharField(max_length=30, choices=NOTIFICATION_CATEGORIES, blank=True, null=True)
    subject = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', 'sent_at']),
            models.Index(fields=['booking', 'notification_type']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.subject}"

class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=30, choices=Notification.NOTIFICATION_CATEGORIES, blank=True, null=True)
    notification_type = models.CharField(max_length=20, choices=Notification.NOTIFICATION_TYPES, blank=True, null=True)
    subject_template = models.CharField(max_length=200, blank=True, null=True)
    message_template = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name