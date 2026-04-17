from django.urls import path
from .views import ProjectAPIView

urlpatterns = [
    path('', ProjectAPIView.as_view(), name='projects'),
    path('<int:id>/', ProjectAPIView.as_view(), name='project-delete'),
]