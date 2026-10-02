from .utils import log_audit

class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/admin-panel/') and request.user.is_authenticated:
            ip = self.get_client_ip(request)
            user_profile = getattr(request.user, 'profile', None)
            log_audit(
                user_profile=user_profile,
                action=f"WEB_REQUEST_{request.method}",
                object_type="AdminPath",
                object_id=request.path,
                ip_address=ip,
                metadata={'status_code': response.status_code}
            )
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
