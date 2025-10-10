# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Booking
from .forms import BookingForm


# ✅ 1. Booking Form Page
@login_required
def booking_create_view(request):
    form = BookingForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        booking = form.save(commit=False)
        booking.citizen = request.user
        booking.save()
        messages.success(request, "Your booking was submitted successfully!")
        return redirect('my_bookings')
    return render(request, 'bookings/booking_form.html', {'form': form})


# ✅ 2. My Bookings Page (list + actions)
@login_required
def my_bookings_view(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    bookings = Booking.objects.filter(citizen=request.user)

    if query:
        bookings = bookings.filter(
            Q(service__name__icontains=query) |
            Q(branch__name__icontains=query)
        )
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    if date_filter:
        bookings = bookings.filter(booking_date=date_filter)

    paginator = Paginator(bookings.order_by('-booking_date', '-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'bookings': page_obj,
        'query': query,
        'status_filter': status_filter,
        'date_filter': date_filter,
    }
    return render(request, 'bookings/my_bookings.html', context)


# ✅ 3. Cancel Booking (AJAX)
@login_required
def booking_cancel_view(request, pk):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid request")
    booking = get_object_or_404(Booking, pk=pk, citizen=request.user)
    if booking.status in ['cancelled', 'completed']:
        return JsonResponse({'success': False, 'message': 'Cannot cancel this booking'})
    booking.status = 'cancelled'
    booking.save()
    return JsonResponse({'success': True})


# ✅ 4. Edit Booking (AJAX)
@login_required
def booking_edit_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk, citizen=request.user)
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'errors': form.errors})

    form = BookingForm(instance=booking)
    html = render(request, 'bookings/partials/edit_form.html', {'form': form, 'booking': booking}).content.decode('utf-8')
    return JsonResponse({'form_html': html})


