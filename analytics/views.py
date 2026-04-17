from rest_framework import views, permissions
from rest_framework.response import Response
from tasks.models import Task
from projects.models import Project
from teams.models import Team
from django.utils import timezone

class AnalyticsAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total_tasks = Task.objects.count()
        completed_tasks = Task.objects.filter(status="Completed").count()
        overdue_tasks = Task.objects.filter(
            due_date__lt=timezone.now().date(), 
            status__in=["Todo", "In Progress"]
        ).count()

        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(status="Active").count()
        completed_projects = Project.objects.filter(status="Completed").count()

        total_teams = Team.objects.count()

        data = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "total_teams": total_teams,
        }
        return Response(data)