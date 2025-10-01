from django.contrib import admin
from .models import Report, ReportTemplate


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "report_type",
        "branch",
        "service",
        "start_date",
        "end_date",
        "generated_by",
        "generated_at",
        "report_file",
    )
    list_filter = ("report_type", "branch", "service", "generated_at")
    search_fields = (
        "name",
        "branch__name",
        "service__name",
        "generated_by__username",
        "generated_by__email",
    )
    ordering = ("-generated_at",)
    readonly_fields = ("generated_at",)


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "template_type",
        "active",
    )
    list_filter = ("template_type", "active")
    search_fields = ("name", "fields")
    ordering = ("name",)
