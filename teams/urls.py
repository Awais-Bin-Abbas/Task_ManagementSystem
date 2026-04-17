from django.urls import path
from .views import TeamAPIView  # <-- matches your teams/views.py class

urlpatterns = [
    path('', TeamAPIView.as_view(), name='teams-api'),
    path('<int:id>/', TeamAPIView.as_view(), name='delete-team'),
]