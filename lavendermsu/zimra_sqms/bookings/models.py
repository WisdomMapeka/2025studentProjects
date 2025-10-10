from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import User, Service, Branch
import uuid

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )
    
    PRIORITY_CHOICES = (
        ('normal', 'Normal'),
        ('priority', 'Priority'),
        ('vip', 'VIP'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizen = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, blank=True, null=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)
    booking_date = models.DateField()
    booking_time = models.TimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal', blank=True, null=True)
    special_requirements = models.TextField(blank=True, null=True)
    token_number = models.CharField(max_length=10, blank=True, null=True)
    estimated_wait_time = models.PositiveIntegerField(default=0, help_text="Estimated wait time in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['booking_date', 'booking_time']
        indexes = [
            models.Index(fields=['booking_date', 'status']),
            models.Index(fields=['citizen', 'status']),
        ]
    
    def __str__(self):
        return f"Booking {self.token_number} - {self.citizen.username}"

class TimeSlot(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    max_capacity = models.PositiveIntegerField(default=10, blank=True, null=True)
    booked_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('branch', 'service', 'date', 'start_time')
        ordering = ['date', 'start_time']
    
    def is_available(self):
        return self.available and self.booked_count < self.max_capacity
    
    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time} - {self.service.name}"