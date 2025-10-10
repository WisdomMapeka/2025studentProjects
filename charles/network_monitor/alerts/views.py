from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Alert

@login_required
def alert_list(request):
    alerts = Alert.objects.select_related("device", "rule").all()
    return render(request, "alerts/alerts_list.html", {"alerts": alerts})

@login_required
def alert_ack(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id)
    alert.status = "acknowledged"
    alert.save(update_fields=["status"])
    messages.success(request, f"Acknowledged alert for {alert.device.name}.")
    return redirect("alerts_list")

@login_required
def alert_resolve(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id)
    alert.status = "resolved"
    alert.save(update_fields=["status"])
    messages.success(request, f"Resolved alert for {alert.device.name}.")
    return redirect("alerts_list")
