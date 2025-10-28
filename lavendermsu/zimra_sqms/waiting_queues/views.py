from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.utils import timezone
from .models import WaitingQueue
from core.models import Counter
from .send_notifications import send_custom_email, send_sms_via_api
from notifications.models import Notification, NotificationTemplate
from bookings.models import Booking

def queue_list(request):
    queues = WaitingQueue.objects.all().select_related('booking', 'counter')

    # Filters
    status = request.GET.get('status')
    counter_id = request.GET.get('counter')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if status and status != 'all':
        queues = queues.filter(status=status)

    if counter_id and counter_id != 'all':
        queues = queues.filter(counter__id=counter_id)

    if start_date:
        queues = queues.filter(created_at__date__gte=start_date)
    if end_date:
        queues = queues.filter(created_at__date__lte=end_date)

    counters = Counter.objects.all()

    context = {
        'queues': queues,
        'status': status,
        'counters': counters,
    }
    return render(request, 'waiting_queues/queue_list.html', context)


def queue_detail(request, pk):
    queue = get_object_or_404(WaitingQueue, pk=pk)
    return render(request, 'waiting_queues/queue_detail.html', {'queue': queue})


def mark_as_done(request, pk):
    queue = get_object_or_404(WaitingQueue, pk=pk)
    queue.status = 'completed'
    queue.service_duration = int((timezone.now() - queue.serving_start_time).total_seconds() / 60)
    queue.serving_end_time = timezone.now()
    queue.save()

    booking = queue.booking
    booking.status = 'completed'
    booking.save()
    subject = "Service Completed"
    message = f"Dear {queue.booking.citizen.first_name}, your service for booking {queue.booking.token_number} has been completed. Thank you for visiting."
    category='service_completion'

    try:
        send_sms_via_api(queue.booking.citizen.phone_number, message, queue, category)
    except Exception as e:
        print(f"Failed to send SMS: {e}")

    try:
        recipient_list = [queue.booking.citizen.email]
        send_custom_email(subject, message, recipient_list, queue, category)
    except Exception as e:
        print(f"Failed to send completion email: {e}")
    
    return redirect('queue_list')

def start_serving(request, pk):
    queue = get_object_or_404(WaitingQueue, pk=pk)
    queue.status = 'serving'
    queue.called_time = timezone.now()
    queue.serving_start_time = timezone.now()
    queue.save()

    booking = queue.booking
    booking.status = 'serving'
    booking.save()
    subject = "You are being served"
    message = f"Dear {queue.booking.citizen.first_name}, you are now being served for your booking {queue.booking.token_number}."
    category='serving'
    try:
        send_sms_via_api(queue.booking.citizen.phone_number, message, queue, category)
    except Exception as e:
        print(f"Failed to send SMS: {e}")

    try:
        recipient_list = [queue.booking.citizen.email]
        send_custom_email(subject, message, recipient_list, queue, category)
    except Exception as e:
        print(f"Failed to send serving email: {e}")

    return redirect('queue_list')
