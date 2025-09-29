from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Service, Branch, Counter

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'first_name', 'last_name', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'id_number', 'date_of_birth', 'address')
        }),
    )

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'estimated_duration', 'active')
    list_filter = ('category', 'active')
    search_fields = ('name', 'description')

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone_number', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'address')

@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ('branch', 'number', 'service', 'active')
    list_filter = ('branch', 'service', 'active')