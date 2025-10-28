# audittrail/middleware.py
from .models import SiteVisit
from django.utils.deprecation import MiddlewareMixin

class VisitorTrackingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip admin, static, media
        if request.path.startswith('/admin/') or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return

        # Record the visit
        ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        user = request.user if request.user.is_authenticated else None

        SiteVisit.objects.create(
            user=user,
            ip_address=ip,
            user_agent=user_agent,
            path=request.path
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
