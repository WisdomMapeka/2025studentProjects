# bookings/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from bookings.models import Booking
from waiting_queues.models import WaitingQueue

@receiver(post_save, sender=Booking)
def create_waiting_queue_entry(sender, instance, created, **kwargs):
    """
    Automatically create a WaitingQueue entry when a Booking is created.
    """
    if created:
        WaitingQueue.objects.get_or_create(
            booking=instance,
            defaults={
                'booked_date': instance.booking_date,
                'booked_time': instance.booking_time,
                'status': 'waiting',
            }
        )
