from django.urls import path
from .views import AnalyticsAPIView  # <-- matches your analytics/views.py class

urlpatterns = [
    path('', AnalyticsAPIView.as_view(), name='analytics-api'),
]