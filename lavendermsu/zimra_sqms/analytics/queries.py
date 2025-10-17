from django.db.models import Count, Avg, Q, F, IntegerField
from django.db.models.functions import TruncDate, ExtractHour, Coalesce
from django.utils import timezone
from bookings.models import Booking
from waiting_queues.models import WaitingQueue, WaitingQueueMetrics
from core.models import Branch, Service

def base_filters(filters):
    """Return a Q() you can reuse across queries."""
    q = Q(booking_date__range=(filters['start_date'], filters['end_date']))
    if filters.get('branch'):
        q &= Q(branch=filters['branch'])
    if filters.get('service'):
        q &= Q(service=filters['service'])
    return q

def kpis(filters):
    q = base_filters(filters)

    total = Booking.objects.filter(q).count()
    completed = Booking.objects.filter(q, status='completed').count()
    cancelled = Booking.objects.filter(q, status='cancelled').count()
    no_show = Booking.objects.filter(q, status='no_show').count()

    # avg wait & service from WaitingQueue (joined via booking)
    wq = WaitingQueue.objects.filter(
        booking__booking_date__range=(filters['start_date'], filters['end_date'])
    )
    if filters.get('branch'):
        wq = wq.filter(booking__branch=filters['branch'])
    if filters.get('service'):
        wq = wq.filter(booking__service=filters['service'])

    avg_wait = wq.aggregate(v=Avg('wait_duration'))['v'] or 0
    avg_service = wq.aggregate(v=Avg('service_duration'))['v'] or 0

    completion_rate = round((completed / total) * 100, 1) if total else 0.0
    cancel_rate = round((cancelled / total) * 100, 1) if total else 0.0
    no_show_rate = round((no_show / total) * 100, 1) if total else 0.0

    return {
        'total': total,
        'completed': completed,
        'completion_rate': completion_rate,
        'avg_wait': int(avg_wait),
        'avg_service': int(avg_service),
        'cancel_rate': cancel_rate,
        'no_show_rate': no_show_rate,
    }

def bookings_timeseries(filters):
    q = base_filters(filters)
    qs = (Booking.objects
          .filter(q)
          .annotate(day=TruncDate('booking_date'))
          .values('day')
          .annotate(count=Count('id'))
          .order_by('day'))
    labels = [x['day'].isoformat() for x in qs]
    data = [x['count'] for x in qs]
    return {'labels': labels, 'data': data}

def status_distribution(filters):
    q = base_filters(filters)
    qs = (Booking.objects
          .filter(q)
          .values('status')
          .annotate(count=Count('id'))
          .order_by())
    return {row['status']: row['count'] for row in qs}

def branch_comparison(filters):
    q = base_filters(filters)
    qs = (Booking.objects
          .filter(q)
          .values('branch__name')
          .annotate(count=Count('id'))
          .order_by('-count')[:10])
    labels = [x['branch__name'] or '—' for x in qs]
    data = [x['count'] for x in qs]
    return {'labels': labels, 'data': data}

def service_leaderboard(filters, limit=10):
    q = base_filters(filters)
    qs = (Booking.objects
          .filter(q)
          .values('service__name')
          .annotate(count=Count('id'))
          .order_by('-count')[:limit])
    return [{'service': x['service__name'] or '—', 'count': x['count']} for x in qs]

def hourly_heatmap(filters):
    """
    Bookings per hour (0-23) over the window. We’ll count using booking_time when present,
    else fall back to created_at hour for robustness.
    """
    q = base_filters(filters)
    # prefer booking_time; if null, use created_at
    with_time = Booking.objects.filter(q, booking_time__isnull=False)\
                   .annotate(h=ExtractHour('booking_time'))
    with_created = Booking.objects.filter(q, booking_time__isnull=True)\
                    .annotate(h=ExtractHour('created_at'))

    from django.db.models import Value
    from django.db.models.functions import Coalesce

    # Use a union and aggregate by h
    unioned = with_time.values('h').union(with_created.values('h'))
    hours = {h: 0 for h in range(24)}
    # Re-run aggregation per hour (sqlite-friendly approach)
    for h in range(24):
        hours[h] = Booking.objects.filter(q).filter(
            Q(booking_time__isnull=False, **{'booking_time__hour': h}) |
            Q(booking_time__isnull=True, **{'created_at__hour': h})
        ).count()
    labels = [f'{h:02d}:00' for h in range(24)]
    data = [hours[h] for h in range(24)]
    return {'labels': labels, 'data': data}
