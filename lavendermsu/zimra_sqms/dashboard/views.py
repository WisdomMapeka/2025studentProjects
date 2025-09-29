from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from bookings.models import Booking
from queue.models import Queue
from core.models import Counter, Branch
from django.db.models import Count, Avg

def staff_required(user):
    return user.is_authenticated and user.user_type in ['staff', 'admin']

@login_required
@user_passes_test(staff_required)
def staff_dashboard(request):
    today = timezone.now().date()
    branch = request.user.branch if hasattr(request.user, 'branch') else None
    
    # Get today's statistics
    today_bookings = Booking.objects.filter(booking_date=today)
    if branch:
        today_bookings = today_bookings.filter(branch=branch)
    
    today_stats = {
        'total': today_bookings.count(),
        'completed': today_bookings.filter(status='completed').count(),
        'in_progress': today_bookings.filter(status='in_progress').count(),
        'waiting': today_bookings.filter(status='confirmed').count(),
    }
    
    # Get current queue
    current_queue = Queue.objects.filter(status__in=['waiting', 'called']).select_related('booking')
    if branch:
        current_queue = current_queue.filter(booking__branch=branch)
    
    context = {
        'today_stats': today_stats,
        'current_queue': current_queue.order_by('queue_number')[:10],
        'branch': branch,
    }
    
    return render(request, 'dashboard/staff_dashboard.html', context)

@login_required
@user_passes_test(staff_required)
def counter_dashboard(request, counter_id):
    counter = Counter.objects.get(id=counter_id)
    current_serving = Queue.objects.filter(counter=counter, status='serving').first()
    next_in_line = Queue.objects.filter(status='waiting').order_by('queue_number').first()
    
    context = {
        'counter': counter,
        'current_serving': current_serving,
        'next_in_line': next_in_line,
    }
    
    return render(request, 'dashboard/counter_dashboard.html', context)