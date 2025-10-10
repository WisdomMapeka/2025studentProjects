from django.contrib import admin
from .models import DeviceType, NetworkDevice, DeviceStatusHistory, SNMPConfiguration
from monitoring.tasks import check_device_task


# ---------- Inline Configuration ----------
class SNMPConfigurationInline(admin.StackedInline):
    """Inline SNMP configuration inside Network Device"""
    model = SNMPConfiguration
    extra = 0
    can_delete = True
    fieldsets = (
        (None, {
            "fields": ("version", "community", "username", "auth_password", "priv_password")
        }),
    )
    verbose_name_plural = "SNMP Configuration"


# ---------- Device Type Admin ----------
@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    """Admin configuration for Device Types"""
    list_display = ("name", "description")
    search_fields = ("name", "description")
    ordering = ("name",)



# ---------- SNMP Configuration Admin ----------
@admin.register(SNMPConfiguration)
class SNMPConfigurationAdmin(admin.ModelAdmin):
    """Admin configuration for SNMP settings"""
    list_display = (
        "device", "version", "community", "username"
    )
    list_filter = ("version",)
    search_fields = ("device__name", "community", "username")
    ordering = ("device__name",)
    fieldsets = (
        ("SNMP Details", {
            "fields": ("device", "version", "community")
        }),
        ("SNMPv3 Authentication", {
            "fields": ("username", "auth_password", "priv_password"),
            "classes": ("collapse",),
        }),
    )



@admin.register(NetworkDevice)
class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "ip_address", "device_type", "status", "is_active", "last_checked", "response_time")
    list_filter = ("device_type", "status", "is_active", "use_snmp")
    search_fields = ("name", "ip_address", "location", "description")
    actions = ["action_check_now", "action_activate", "action_deactivate"]

    @admin.action(description="Check selected devices now (async)")
    def action_check_now(self, request, queryset):
        for d in queryset:
            check_device_task.delay(d.id)

    @admin.action(description="Activate monitoring")
    def action_activate(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate monitoring")
    def action_deactivate(self, request, queryset):
        queryset.update(is_active=False)

@admin.register(DeviceStatusHistory)
class DeviceStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("device", "status", "response_time", "timestamp")
    list_filter = ("status", "timestamp")
    search_fields = ("device__name", "device__ip_address")
    date_hierarchy = "timestamp"
