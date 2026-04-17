from django.urls import path
from .views import TaskAPIView  # <-- matches your tasks/views.py class

urlpatterns = [
    path('', TaskAPIView.as_view(), name='tasks-api'),
    path('<int:id>/', TaskAPIView.as_view(), name='tasks-api'),
]