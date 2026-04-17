from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.serializers import CustomTokenObtainPairSerializer
from accounts.views import ForgotPasswordView, ResetPasswordView, ChangePasswordView, PasswordRequestsView, ResolvePasswordRequestView


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # =========================
    # AUTH (JWT)
    # =========================
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/password-requests/', PasswordRequestsView.as_view(), name='password-requests'),
    path('auth/resolve-password-request/', ResolvePasswordRequestView.as_view(), name='resolve-password-request'),

    # =========================
    # APPS
    # =========================
    path('users/', include('accounts.urls')),   # ✅ USERS API (FIXED)
    path('teams/', include('teams.urls')),
    path('projects/', include('projects.urls')),
    path('tasks/', include('tasks.urls')),
    path('analytics/', include('analytics.urls')),

    # =========================
    # API DOCUMENTATION
    # =========================
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]