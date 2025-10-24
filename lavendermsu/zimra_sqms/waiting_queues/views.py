from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.utils import timezone
from .models import WaitingQueue
from core.models import Counter

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
    return redirect('queue_list')

def start_serving(request, pk):
    queue = get_object_or_404(WaitingQueue, pk=pk)
    queue.status = 'serving'
    queue.serving_start_time = timezone.now()
    queue.save()
    return redirect('queue_list')
