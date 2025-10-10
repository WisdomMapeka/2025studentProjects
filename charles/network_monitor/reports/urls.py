from django.urls import path
from . import views

urlpatterns = [
    path("uptime/csv/", views.uptime_csv, name="uptime_csv"),
]
