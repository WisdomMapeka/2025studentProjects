# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('book/', views.booking_create_view, name='booking_create'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),

    # AJAX endpoints
    path('my-bookings/<uuid:pk>/cancel/', views.booking_cancel_view, name='booking_cancel'),
    path('my-bookings/<uuid:pk>/edit/', views.booking_edit_view, name='booking_edit'),
]
