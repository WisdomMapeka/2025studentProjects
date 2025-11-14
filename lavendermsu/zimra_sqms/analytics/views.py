from django.views.generic import TemplateView, FormView
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncDate, ExtractHour
from django import forms
from django.utils import timezone
import csv
import io
import datetime
from bookings.models import Booking
from waiting_queues.models import WaitingQueue

class AnalyticsFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    branch = forms.ModelChoiceField(queryset=Booking.objects.values_list('branch', flat=True).distinct(), required=False)
    service = forms.ModelChoiceField(queryset=Booking.objects.values_list('service', flat=True).distinct(), required=False)

def get_analytics_filters(form_data):
    """Extract and validate analytics filters from form data"""
    today = timezone.localdate()
    filters = {
        'start_date': today - timezone.timedelta(days=29),
        'end_date': today,
        'branch': None,
        'service': None,
    }
    
    # Update with form data if provided and valid
    if form_data.get('start_date'):
        filters['start_date'] = form_data['start_date']
    if form_data.get('end_date'):
        filters['end_date'] = form_data['end_date']
    if form_data.get('branch'):
        filters['branch'] = form_data['branch']
    if form_data.get('service'):
        filters['service'] = form_data['service']
    
    # Validate date range
    if filters['start_date'] and filters['end_date'] and filters['start_date'] > filters['end_date']:
        raise forms.ValidationError('Start date cannot be after end date.')
    
    return filters

# Query functions using only Booking and WaitingQueue models
def kpis(filters):
    """Calculate KPIs using only Booking and WaitingQueue models"""
    booking_qs = Booking.objects.filter(
        booking_date__range=(filters['start_date'], filters['end_date'])
    )
    
    if filters.get('branch'):
        booking_qs = booking_qs.filter(branch=filters['branch'])
    if filters.get('service'):
        booking_qs = booking_qs.filter(service=filters['service'])
    
    total = booking_qs.count()
    completed = booking_qs.filter(status='completed').count()
    
    # Calculate completion rate
    completion_rate = round((completed / total * 100) if total > 0 else 0, 1)
    
    # Calculate cancel and no-show rates
    cancelled = booking_qs.filter(status='cancelled').count()
    no_show = booking_qs.filter(status='no_show').count()
    cancel_rate = round((cancelled / total * 100) if total > 0 else 0, 1)
    no_show_rate = round((no_show / total * 100) if total > 0 else 0, 1)
    
    # Get average wait times from WaitingQueue
    wait_qs = WaitingQueue.objects.filter(
        booking__booking_date__range=(filters['start_date'], filters['end_date'])
    )
    if filters.get('branch'):
        wait_qs = wait_qs.filter(booking__branch=filters['branch'])
    if filters.get('service'):
        wait_qs = wait_qs.filter(booking__service=filters['service'])
    
    avg_wait_result = wait_qs.aggregate(avg=Avg('wait_duration'))
    avg_service_result = wait_qs.aggregate(avg=Avg('service_duration'))
    
    avg_wait = round(avg_wait_result['avg'] or 0, 1)
    avg_service = round(avg_service_result['avg'] or 0, 1)
    
    return {
        'total': total,
        'completed': completed,
        'completion_rate': completion_rate,
        'avg_wait': avg_wait,
        'avg_service': avg_service,
        'cancel_rate': cancel_rate,
        'no_show_rate': no_show_rate,
    }

def bookings_timeseries(filters):
    """Get bookings over time using Booking model"""
    qs = Booking.objects.filter(
        booking_date__range=(filters['start_date'], filters['end_date'])
    )
    
    if filters.get('branch'):
        qs = qs.filter(branch=filters['branch'])
    if filters.get('service'):
        qs = qs.filter(service=filters['service'])
    
    # Group by date and count
    timeseries_data = qs.values('booking_date').annotate(
        count=Count('id')
    ).order_by('booking_date')
    
    # Create complete date range
    # Convert string dates to datetime.date objects if they're strings
    if isinstance(filters['start_date'], str):
        filters['start_date'] = datetime.datetime.strptime(filters['start_date'], '%Y-%m-%d').date()

    if isinstance(filters['end_date'], str):
        filters['end_date'] = datetime.datetime.strptime(filters['end_date'], '%Y-%m-%d').date()

    date_range = []
    current_date = filters['start_date']
    while current_date <= filters['end_date']:
        date_range.append(current_date)
        current_date += datetime.timedelta(days=1)

    # Map counts to dates
    count_map = {item['booking_date']: item['count'] for item in timeseries_data}
    counts = [count_map.get(date, 0) for date in date_range]

    labels = [date.strftime('%Y-%m-%d') for date in date_range]

    return {
        'labels': labels,
        'data': counts,
    }

def status_distribution(filters):
    """Get status distribution using Booking model"""
    qs = Booking.objects.filter(
        booking_date__range=(filters['start_date'], filters['end_date'])
    )
    
    if filters.get('branch'):
        qs = qs.filter(branch=filters['branch'])
    if filters.get('service'):
        qs = qs.filter(service=filters['service'])
    
    status_data = qs.values('status').annotate(
        count=Count('id')
    )
    
    # Convert to dictionary format
    result = {item['status']: item['count'] for item in status_data}
    
    return result

def branch_comparison(filters):
    """Compare branches using Booking model"""
    qs = Booking.objects.filter(
        booking_date__range=(filters['start_date'], filters['end_date'])
    )
    
    if filters.get('service'):
        qs = qs.filter(service=filters['service'])
    
    branch_data = qs.values('branch__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]  # Top 10 branches
    
    labels = [item['branch__name'] or 'Unknown' for item in branch_data]
    counts = [item['count'] for item in branch_data]
    
    return {
        'labels': labels,
        'data': counts,
    }

def hourly_heatmap(filters):
    """Get hourly distribution using Booking model"""
    qs = Booking.objects.filter(
        booking_date__range=(filters['start_date'], filters['end_date'])
    ).exclude(booking_time__isnull=True)
    
    if filters.get('branch'):
        qs = qs.filter(branch=filters['branch'])
    if filters.get('service'):
        qs = qs.filter(service=filters['service'])
    
    # Extract hour and count
    hourly_data = qs.annotate(
        hour=ExtractHour('booking_time')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    # Create complete hour range (0-23)
    hours = list(range(24))
    count_map = {item['hour']: item['count'] for item in hourly_data}
    counts = [count_map.get(hour, 0) for hour in hours]
    labels = [f"{hour:02d}:00" for hour in hours]
    
    return {
        'labels': labels,
        'data': counts,
    }

def service_leaderboard(filters, limit=10):
    """Get top services using Booking model"""
    qs = Booking.objects.filter(
        booking_date__range=(filters['start_date'], filters['end_date'])
    )
    
    if filters.get('branch'):
        qs = qs.filter(branch=filters['branch'])
    
    service_data = qs.values('service__name').annotate(
        count=Count('id')
    ).order_by('-count')[:limit]
    
    result = []
    for item in service_data:
        result.append({
            'service': item['service__name'] or 'Unknown',
            'count': item['count']
        })
    
    return result

class DashboardView(FormView):
    template_name = 'analytics/dashboard.html'
    form_class = AnalyticsFilterForm

    def form_valid(self, form):
        filters = form.cleaned_data
        context = self.build_context(filters, form)
        return render(self.request, self.template_name, context)

    def get(self, request, *args, **kwargs):
        form = self.form_class(request.GET or None)
        
        try:
            if form.is_valid():
                filters = form.cleaned_data
            else:
                # Use GET data directly for filtering, with defaults
                filters = get_analytics_filters(request.GET)
        except forms.ValidationError as e:
            # If there's a validation error, add it to the form and use defaults
            form.add_error(None, e)
            filters = get_analytics_filters({})
        
        context = self.build_context(filters, form)
        return render(request, self.template_name, context)

    def build_context(self, filters, form):
        kpi_data = kpis(filters)
        ts_data = bookings_timeseries(filters)
        status_data = status_distribution(filters)
        branches_data = branch_comparison(filters)
        heat_data = hourly_heatmap(filters)
        top_services = service_leaderboard(filters, limit=10)

        return {
            'form': form,
            'filters': filters,
            'kpi': kpi_data,
            'ts': ts_data,
            'status': status_data,
            'branches': branches_data,
            'heat': heat_data,
            'top_services': top_services,
        }

class ReportsView(TemplateView):
    template_name = 'analytics/reports.html'

def export_csv(request):
    form = AnalyticsFilterForm(request.GET or None)
    
    # Safe way to get filters
    if form.is_valid():
        filters = form.cleaned_data
    else:
        # Build default filters manually
        today = timezone.localdate()
        filters = {
            'start_date': today - timezone.timedelta(days=29),
            'end_date': today,
            'branch': None,
            'service': None,
        }
        # Update with any valid GET parameters
        for field_name in ['start_date', 'end_date', 'branch', 'service']:
            if field_name in request.GET:
                try:
                    filters[field_name] = form.fields[field_name].to_python(request.GET[field_name])
                except (ValueError, TypeError):
                    pass

    # Export using Booking model only
    qs = Booking.objects.filter(
        booking_date__range=(filters['start_date'], filters['end_date'])
    )
    if filters.get('branch'):
        qs = qs.filter(branch=filters['branch'])
    if filters.get('service'):
        qs = qs.filter(service=filters['service'])

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "token_number", "booking_date", "booking_time", "status", "priority",
        "citizen", "service", "branch", "estimated_wait_time", "created_at"
    ])
    for b in qs.select_related('citizen', 'service', 'branch'):
        writer.writerow([
            b.token_number,
            b.booking_date,
            b.booking_time or '',
            b.status,
            b.priority,
            b.citizen.username if b.citizen else '',
            b.service.name if b.service else '',
            b.branch.name if b.branch else '',
            b.estimated_wait_time,
            b.created_at.isoformat(),
        ])
    resp = HttpResponse(buffer.getvalue(), content_type='text/csv')
    filename = f"bookings_{filters['start_date']}_{filters['end_date']}.csv"
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp

def export_xlsx(request):
    # Optional: Excel export (requires openpyxl)
    try:
        from openpyxl import Workbook
    except ImportError:
        return HttpResponse("Excel export requires openpyxl package", status=500)
        
    form = AnalyticsFilterForm(request.GET or None)
    
    # Safe way to get filters
    if form.is_valid():
        filters = form.cleaned_data
    else:
        # Build default filters manually
        today = timezone.localdate()
        filters = {
            'start_date': today - timezone.timedelta(days=29),
            'end_date': today,
            'branch': None,
            'service': None,
        }
        # Update with any valid GET parameters
        for field_name in ['start_date', 'end_date', 'branch', 'service']:
            if field_name in request.GET:
                try:
                    filters[field_name] = form.fields[field_name].to_python(request.GET[field_name])
                except (ValueError, TypeError):
                    pass

    qs = Booking.objects.filter(
        booking_date__range=(filters['start_date'], filters['end_date'])
    )
    if filters.get('branch'):
        qs = qs.filter(branch=filters['branch'])
    if filters.get('service'):
        qs = qs.filter(service=filters['service'])

    wb = Workbook()
    ws = wb.active
    ws.title = "Bookings"
    ws.append(["Token", "Date", "Time", "Status", "Priority", "Citizen", "Service", "Branch", "Est. Wait", "Created"])

    for b in qs.select_related('citizen', 'service', 'branch'):
        ws.append([
            b.token_number,
            str(b.booking_date),
            str(b.booking_time or ''),
            b.status,
            b.priority,
            b.citizen.username if b.citizen else '',
            b.service.name if b.service else '',
            b.branch.name if b.branch else '',
            b.estimated_wait_time,
            b.created_at.isoformat(),
        ])

    fn = f"bookings_{filters['start_date']}_{filters['end_date']}.xlsx"
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    resp = HttpResponse(
        stream.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp['Content-Disposition'] = f'attachment; filename="{fn}"'
    return resp