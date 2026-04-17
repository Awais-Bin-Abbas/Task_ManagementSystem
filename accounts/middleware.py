from django.utils import timezone
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication

class PasswordExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow auth paths (like change-password, login, etc.)
        if not request.path.startswith('/auth/') and not request.path.startswith('/admin/'):
            auth = JWTAuthentication()
            try:
                user_auth_tuple = auth.authenticate(request)
                if user_auth_tuple:
                    user = user_auth_tuple[0]
                    if user.password_expires_at and user.password_expires_at < timezone.now():
                        return JsonResponse(
                            {"error": "Password has expired. Please request a new password reset from your manager."},
                            status=403
                        )
            except Exception:
                pass
        return self.get_response(request)
