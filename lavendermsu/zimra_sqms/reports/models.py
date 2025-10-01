from django.db import models
from core.models import Branch, Service

class Report(models.Model):
    REPORT_TYPES = (
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('yearly', 'Yearly Report'),
        ('custom', 'Custom Report'),
    )
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True)
    generated_by = models.ForeignKey('core.User', on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    report_file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    def __str__(self):
        return self.name

class ReportTemplate(models.Model):
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=Report.REPORT_TYPES)
    fields = models.JSONField(help_text="JSON configuration of report fields")
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name