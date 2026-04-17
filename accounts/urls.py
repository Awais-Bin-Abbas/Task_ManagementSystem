# accounts/urls.py
from django.urls import path
from .views import UserAPIView

urlpatterns = [
    path('register/', UserAPIView.as_view(), name='users'),
    path('register/<int:id>/', UserAPIView.as_view(), name='user-detail'),
]