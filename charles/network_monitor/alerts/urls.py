from django.urls import path
from . import views

urlpatterns = [
    path("", views.alert_list, name="alerts_list"),
    path("<int:alert_id>/ack/", views.alert_ack, name="alert_ack"),
    path("<int:alert_id>/resolve/", views.alert_resolve, name="alert_resolve"),
]
