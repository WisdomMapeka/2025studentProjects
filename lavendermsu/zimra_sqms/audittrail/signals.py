# audittrail/signals.py
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import AuditTrail

def get_client_ip(request):
    """Get client IP from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditTrail.objects.create(
        user=user,
        action='login',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    AuditTrail.objects.create(
        user=user,
        action='logout',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get('username', 'Unknown')
    # Try to get user instance if exists
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None

    AuditTrail.objects.create(
        user=user,
        action='failed_login',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        extra_info=f"Attempted username: {username}"
    )
