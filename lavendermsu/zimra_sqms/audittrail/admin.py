# audittrail/admin.py
from django.contrib import admin
from .models import AuditTrail

@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'timestamp')
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('user__username', 'ip_address', 'extra_info')


# audittrail/admin.py
from django.contrib import admin
from .models import AuditTrail, SiteVisit

@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'path', 'timestamp')
    search_fields = ('user__username', 'ip_address', 'path')
    list_filter = ('timestamp',)
