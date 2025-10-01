from django.db import models
from core.models import Counter
from bookings.models import Booking

class WaitingQueue(models.Model):
    STATUS_CHOICES = (
        ('waiting', 'Waiting'),
        ('called', 'Called'),
        ('serving', 'Serving'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    counter = models.ForeignKey(Counter, on_delete=models.SET_NULL, null=True, blank=True)
    queue_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    called_time = models.DateTimeField(null=True, blank=True)
    serving_start_time = models.DateTimeField(null=True, blank=True)
    serving_end_time = models.DateTimeField(null=True, blank=True)
    wait_duration = models.PositiveIntegerField(default=0, help_text="Wait duration in minutes")
    service_duration = models.PositiveIntegerField(default=0, help_text="Service duration in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['queue_number']
        indexes = [
            models.Index(fields=['status', 'queue_number']),
            models.Index(fields=['booking', 'status']),
        ]
    
    def __str__(self):
        return f"Queue {self.queue_number} - {self.booking.token_number}"

class  WaitingQueueMetrics(models.Model):
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE)
    service = models.ForeignKey('core.Service', on_delete=models.CASCADE)
    date = models.DateField()
    total_bookings = models.PositiveIntegerField(default=0)
    completed_bookings = models.PositiveIntegerField(default=0)
    average_wait_time = models.PositiveIntegerField(default=0)
    average_service_time = models.PositiveIntegerField(default=0)
    peak_hour = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('branch', 'service', 'date')
    
    def __str__(self):
        return f"Metrics - {self.branch.name} - {self.service.name} - {self.date}"