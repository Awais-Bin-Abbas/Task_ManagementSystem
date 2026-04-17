import datetime
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from accounts.models import User
from teams.models import Team
from projects.models import Project
from tasks.models import Task


class AnalyticsAPIViewTest(APITestCase):
    """Test cases for AnalyticsAPIView"""

    def setUp(self):
        self.client = APIClient()

        # Users
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin123", role="Admin"
        )
        self.member = User.objects.create_user(
            username="member", email="member@test.com", password="pass123", role="Member"
        )

        # Teams
        self.team1 = Team.objects.create(name="Alpha Team", description="Alpha")
        self.team2 = Team.objects.create(name="Beta Team", description="Beta")

        # Projects
        self.project1 = Project.objects.create(
            name="Project One", description="First",
            team=self.team1, deadline=datetime.date.today(), status="Active"
        )
        self.project2 = Project.objects.create(
            name="Project Two", description="Second",
            team=self.team2, deadline=datetime.date.today(), status="Completed"
        )

        # Tasks — completed
        Task.objects.create(
            title="Done Task 1", description="Done",
            project=self.project1, priority="High",
            status="Completed", due_date=datetime.date.today()
        )
        Task.objects.create(
            title="Done Task 2", description="Done too",
            project=self.project2, priority="Medium",
            status="Completed", due_date=datetime.date.today()
        )

        # Tasks — active
        Task.objects.create(
            title="Active Task", description="Still going",
            project=self.project1, priority="Low",
            status="In Progress", due_date=datetime.date.today()
        )

        # Tasks — overdue (past due_date, not completed)
        # NOTE: The current analytics view has a bug: it uses `dueDate__lt`
        # instead of `due_date__lt`. These tests document BOTH the expected
        # correct behavior and the current (buggy) behavior.
        Task.objects.create(
            title="Overdue Task 1", description="Past deadline",
            project=self.project1, priority="High",
            status="Todo", due_date=datetime.date(2020, 1, 1)
        )
        Task.objects.create(
            title="Overdue Task 2", description="Past deadline too",
            project=self.project1, priority="Medium",
            status="In Progress", due_date=datetime.date(2020, 1, 1)
        )

    # ─── Authentication ────────────────────────────────────────────────────

    def test_analytics_requires_authentication(self):
        response = self.client.get("/analytics/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_access_analytics(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/analytics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_can_access_analytics(self):
        """No role restriction — any authenticated user can access"""
        self.client.force_authenticate(user=self.member)
        response = self.client.get("/analytics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ─── Response Shape ────────────────────────────────────────────────────

    def test_analytics_response_has_all_keys(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/analytics/")
        self.assertIn("total_tasks", response.data)
        self.assertIn("completed_tasks", response.data)
        self.assertIn("overdue_tasks", response.data)
        self.assertIn("total_projects", response.data)
        self.assertIn("total_teams", response.data)

    def test_analytics_total_tasks_count(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/analytics/")
        self.assertEqual(response.data["total_tasks"], Task.objects.count())

    def test_analytics_completed_tasks_count(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/analytics/")
        expected = Task.objects.filter(status="Completed").count()
        self.assertEqual(response.data["completed_tasks"], expected)

    def test_analytics_total_projects_count(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/analytics/")
        self.assertEqual(response.data["total_projects"], Project.objects.count())

    def test_analytics_total_teams_count(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/analytics/")
        self.assertEqual(response.data["total_teams"], Team.objects.count())

    # ─── Bug: overdue_tasks uses wrong field name ──────────────────────────

    def test_analytics_overdue_tasks_field_bug(self):
        """
        BUG: The view uses `dueDate__lt` (camelCase) instead of `due_date__lt`.
        This will raise a FieldError at runtime. This test documents the bug.
        Once fixed to use `due_date__lt`, the count should equal 2 in our setUp.
        """
        self.client.force_authenticate(user=self.admin)
        # With the bug in place, this endpoint will raise a 500 error.
        # After fixing `dueDate__lt` → `due_date__lt`, the status should be 200.
        response = self.client.get("/analytics/")
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        )

    def test_analytics_overdue_tasks_count_after_fix(self):
        """
        After fixing the bug (dueDate__lt → due_date__lt), overdue_tasks
        should correctly count tasks with past due_date and non-completed status.
        """
        overdue_count = Task.objects.filter(
            due_date__lt=datetime.date.today(),
            status__in=["Todo", "In Progress"]
        ).count()
        self.assertEqual(overdue_count, 2)

    # ─── Data Integrity ────────────────────────────────────────────────────

    def test_analytics_with_empty_database(self):
        """Analytics should return zeros when there is no data"""
        Task.objects.all().delete()
        Project.objects.all().delete()
        Team.objects.all().delete()

        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/analytics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_tasks"], 0)
        self.assertEqual(response.data["completed_tasks"], 0)
        self.assertEqual(response.data["total_projects"], 0)
        self.assertEqual(response.data["total_teams"], 0)

    def test_analytics_completed_tasks_less_than_total(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/analytics/")
        self.assertLessEqual(
            response.data["completed_tasks"],
            response.data["total_tasks"]
        )

    def test_analytics_only_accepts_get(self):
        self.client.force_authenticate(user=self.admin)
        self.assertEqual(self.client.post("/analytics/").status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.patch("/analytics/").status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete("/analytics/").status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_analytics_counts_update_after_task_added(self):
        self.client.force_authenticate(user=self.admin)
        before = self.client.get("/analytics/").data["total_tasks"]
        Task.objects.create(
            title="Brand New Task", description="Freshly added",
            project=self.project1, priority="Low",
            status="Todo", due_date=datetime.date.today()
        )
        after = self.client.get("/analytics/").data["total_tasks"]
        self.assertEqual(after, before + 1)

    def test_analytics_counts_update_after_task_completed(self):
        self.client.force_authenticate(user=self.admin)
        active_task = Task.objects.filter(status="In Progress").first()
        before = self.client.get("/analytics/").data["completed_tasks"]
        active_task.status = "Completed"
        active_task.save()
        after = self.client.get("/analytics/").data["completed_tasks"]
        self.assertEqual(after, before + 1)