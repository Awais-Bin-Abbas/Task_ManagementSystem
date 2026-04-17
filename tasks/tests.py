import datetime
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from accounts.models import User
from teams.models import Team
from projects.models import Project
from tasks.models import Task


class TaskModelTest(TestCase):
    """Test cases for Task model"""

    def setUp(self):
        self.team = Team.objects.create(name="Dev Team", description="Devs")
        self.project = Project.objects.create(
            name="Alpha", description="Project Alpha",
            team=self.team, deadline=datetime.date.today(), status="Active"
        )
        self.user = User.objects.create_user(
            username="dev", email="dev@test.com", password="pass123", role="Member"
        )

    def test_create_task(self):
        task = Task.objects.create(
            title="Fix login bug",
            description="User can't log in",
            project=self.project,
            assigned_to=self.user,
            priority="High",
            status="Todo",
            due_date=datetime.date.today()
        )
        self.assertEqual(task.title, "Fix login bug")
        self.assertEqual(task.priority, "High")
        self.assertEqual(task.status, "Todo")

    def test_task_priority_choices(self):
        for priority in ["High", "Medium", "Low"]:
            task = Task.objects.create(
                title=f"{priority} Task", description="Test",
                project=self.project, priority=priority,
                status="Todo", due_date=datetime.date.today()
            )
            self.assertEqual(task.priority, priority)

    def test_task_status_choices(self):
        for s in ["Todo", "In Progress", "Review", "Completed"]:
            task = Task.objects.create(
                title=f"{s} Task", description="Test",
                project=self.project, priority="Low",
                status=s, due_date=datetime.date.today()
            )
            self.assertEqual(task.status, s)

    def test_task_assigned_to_null_on_user_delete(self):
        task = Task.objects.create(
            title="Orphan Task", description="Will lose assignee",
            project=self.project, assigned_to=self.user,
            priority="Low", status="Todo", due_date=datetime.date.today()
        )
        self.user.delete()
        task.refresh_from_db()
        self.assertIsNone(task.assigned_to)

    def test_task_deleted_on_project_delete(self):
        task = Task.objects.create(
            title="Cascade Task", description="Will go",
            project=self.project, priority="Low",
            status="Todo", due_date=datetime.date.today()
        )
        self.project.delete()
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_task_auto_timestamps(self):
        task = Task.objects.create(
            title="Timed Task", description="Check times",
            project=self.project, priority="Medium",
            status="Todo", due_date=datetime.date.today()
        )
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)

    def test_task_can_have_no_assignee(self):
        task = Task.objects.create(
            title="Unassigned Task", description="No one owns this",
            project=self.project, priority="Low",
            status="Todo", due_date=datetime.date.today()
        )
        self.assertIsNone(task.assigned_to)


class TaskAPIViewTest(APITestCase):
    """Test cases for TaskAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.team = Team.objects.create(name="Dev Team", description="Devs")
        self.project = Project.objects.create(
            name="Alpha", description="Alpha project",
            team=self.team, deadline=datetime.date.today(), status="Active"
        )
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin123", role="Admin"
        )
        self.manager = User.objects.create_user(
            username="manager", email="manager@test.com",
            password="pass123", role="Manager", team=self.team
        )
        self.member = User.objects.create_user(
            username="member", email="member@test.com",
            password="pass123", role="Member", team=self.team
        )
        self.task = Task.objects.create(
            title="Existing Task",
            description="Already here",
            project=self.project,
            assigned_to=self.member,
            priority="High",
            status="Todo",
            due_date=datetime.date.today()
        )

    def _task_data(self, title="New Task"):
        return {
            "title": title,
            "description": "A task description",
            "project": self.project.id,
            "assigned_to": self.member.id,
            "priority": "Medium",
            "status": "Todo",
            "due_date": str(datetime.date.today())
        }

    # ─── POST (Create Task) ────────────────────────────────────────────────

    def test_authenticated_user_can_create_task(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/tasks/", self._task_data("Admin Task"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Admin Task")

    def test_member_can_create_task(self):
        """No role restriction on task creation"""
        self.client.force_authenticate(user=self.member)
        response = self.client.post("/tasks/", self._task_data("Member Task"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_task_unauthenticated(self):
        response = self.client.post("/tasks/", self._task_data())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_task_with_invalid_project(self):
        self.client.force_authenticate(user=self.admin)
        data = self._task_data()
        data["project"] = 99999
        response = self.client.post("/tasks/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_missing_title(self):
        self.client.force_authenticate(user=self.admin)
        data = self._task_data()
        data["title"] = ""
        response = self.client.post("/tasks/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_invalid_priority(self):
        self.client.force_authenticate(user=self.admin)
        data = self._task_data()
        data["priority"] = "Critical"
        response = self.client.post("/tasks/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_invalid_status(self):
        self.client.force_authenticate(user=self.admin)
        data = self._task_data()
        data["status"] = "Pending"
        response = self.client.post("/tasks/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_invalid_due_date(self):
        self.client.force_authenticate(user=self.admin)
        data = self._task_data()
        data["due_date"] = "not-a-date"
        response = self.client.post("/tasks/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_without_assignee(self):
        """assigned_to is optional (nullable)"""
        self.client.force_authenticate(user=self.admin)
        data = self._task_data()
        data.pop("assigned_to")
        response = self.client.post("/tasks/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # ─── GET (List / Retrieve) ─────────────────────────────────────────────

    def test_get_all_tasks(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get("/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_get_single_task_by_id(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get(f"/tasks/?id={self.task.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Existing Task")

    def test_get_task_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/tasks/?id=99999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_tasks_unauthenticated(self):
        response = self.client.get("/tasks/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ─── PATCH (Partial Update) ────────────────────────────────────────────

    def test_patch_task_success(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            "/tasks/", {"id": self.task.id, "status": "In Progress"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "In Progress")

    def test_patch_task_update_priority(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.patch(
            "/tasks/", {"id": self.task.id, "priority": "Low"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["priority"], "Low")

    def test_patch_task_reassign(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.patch(
            "/tasks/", {"id": self.task.id, "assigned_to": self.manager.id},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["assigned_to"], self.manager.id)

    def test_patch_task_without_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch("/tasks/", {"status": "Completed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_task_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            "/tasks/", {"id": 99999, "status": "Completed"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_task_unauthenticated(self):
        response = self.client.patch(
            "/tasks/", {"id": self.task.id, "status": "Completed"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_task_all_status_transitions(self):
        """Verify every valid status can be set via PATCH"""
        self.client.force_authenticate(user=self.admin)
        for s in ["In Progress", "Review", "Completed", "Todo"]:
            response = self.client.patch(
                "/tasks/", {"id": self.task.id, "status": s}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["status"], s)

    # ─── DELETE ───────────────────────────────────────────────────────────

    def test_delete_task_success(self):
        extra = Task.objects.create(
            title="Delete Me", description="Temp",
            project=self.project, priority="Low",
            status="Todo", due_date=datetime.date.today()
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/tasks/{extra.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Task.objects.filter(id=extra.id).exists())

    def test_delete_task_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete("/tasks/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_task_without_id(self):
        """
        DELETE /tasks/ hits the path('', ...) route which has no id param,
        so the view returns 400 Bad Request.
        """
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete("/tasks/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_task_unauthenticated(self):
        response = self.client.delete(f"/tasks/{self.task.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)