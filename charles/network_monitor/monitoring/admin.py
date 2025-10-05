from django.contrib import admin
from .models import DeviceType, NetworkDevice, DeviceStatusHistory, SNMPConfiguration


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


# ---------- Network Device Admin ----------
@admin.register(NetworkDevice)
class NetworkDeviceAdmin(admin.ModelAdmin):
    """Admin configuration for monitored network devices"""
    list_display = (
        "name", "ip_address", "device_type", "status",
        "is_active", "use_snmp", "monitoring_interval",
        "response_time", "last_checked", "location"
    )
    list_filter = (
        "status", "is_active", "device_type", "use_snmp",
        "location", "created_at", "updated_at"
    )
    search_fields = (
        "name", "ip_address", "mac_address", "location", "description"
    )
    list_editable = ("is_active", "use_snmp", "monitoring_interval")
    readonly_fields = ("created_at", "updated_at", "last_checked")
    ordering = ("name",)
    inlines = [SNMPConfigurationInline]
    list_per_page = 25

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "device_type", "description", "location")
        }),
        ("Network Identifiers", {
            "fields": ("ip_address", "mac_address")
        }),
        ("Monitoring Settings", {
            "fields": ("is_active", "monitoring_interval", "use_snmp", "snmp_community")
        }),
        ("Current Status", {
            "fields": ("status", "response_time", "last_checked")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )


# ---------- Device Status History Admin ----------
@admin.register(DeviceStatusHistory)
class DeviceStatusHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for device status history"""
    list_display = (
        "device", "status", "response_time", "timestamp"
    )
    list_filter = ("status", "timestamp", "device__device_type")
    search_fields = ("device__name", "device__ip_address")
    readonly_fields = ("timestamp",)
    ordering = ("-timestamp",)
    list_per_page = 30

    fieldsets = (
        (None, {
            "fields": ("device", "status", "response_time", "timestamp", "additional_info")
        }),
    )


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
