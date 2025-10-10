from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
from monitoring.models import NetworkDevice, DeviceStatusHistory
import csv

def uptime_csv(request):
    """
    Export per-device uptime percentage for the last 24 hours.
    """
    start = timezone.now() - timedelta(hours=24)
    rows = []
    for d in NetworkDevice.objects.all():
        hist = DeviceStatusHistory.objects.filter(device=d, timestamp__gte=start)
        total = hist.count()
        up = hist.filter(status="up").count()
        pct = round((up / total * 100), 2) if total else 0.00
        rows.append((d.name, d.ip_address, pct, total))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="uptime_last_24h.csv"'
    writer = csv.writer(response)
    writer.writerow(["Device", "IP", "Uptime % (24h)", "Samples"])
    writer.writerows(rows)
    return response
