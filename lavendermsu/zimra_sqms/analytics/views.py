from django.views.generic import TemplateView, FormView
from django.shortcuts import render
from django.http import HttpResponse
from .forms import AnalyticsFilterForm
from . import queries
import csv
import io
import datetime
from django import forms
from django.utils import timezone








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
        # Your existing build_context method remains the same
        kpi = queries.kpis(filters)
        ts = queries.bookings_timeseries(filters)
        status = queries.status_distribution(filters)
        branches = queries.branch_comparison(filters)
        heat = queries.hourly_heatmap(filters)
        top_services = queries.service_leaderboard(filters, limit=10)

        return {
            'form': form,
            'filters': filters,
            'kpi': kpi,
            'ts': ts,
            'status': status,
            'branches': branches,
            'heat': heat,
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

    # Basic export: Bookings with core fields
    from bookings.models import Booking
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
        "token_number","booking_date","booking_time","status","priority",
        "citizen","service","branch","estimated_wait_time","created_at"
    ])
    for b in qs.select_related('citizen','service','branch'):
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
    from openpyxl import Workbook
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

    from bookings.models import Booking
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
    ws.append(["Token","Date","Time","Status","Priority","Citizen","Service","Branch","Est. Wait","Created"])

    for b in qs.select_related('citizen','service','branch'):
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

    from django.utils import timezone
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