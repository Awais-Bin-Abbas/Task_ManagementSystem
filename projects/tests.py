import datetime
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from accounts.models import User
from teams.models import Team
from projects.models import Project


class ProjectModelTest(TestCase):
    """Test cases for Project model"""

    def setUp(self):
        self.team = Team.objects.create(name="Dev Team", description="Devs")

    def test_create_project(self):
        project = Project.objects.create(
            name="Alpha Project",
            description="First project",
            team=self.team,
            deadline=datetime.date(2025, 12, 31),
            status="Active"
        )
        self.assertEqual(project.name, "Alpha Project")
        self.assertEqual(project.status, "Active")
        self.assertEqual(project.team, self.team)

    def test_project_status_choices(self):
        for s in ["Active", "Completed"]:
            p = Project.objects.create(
                name=f"{s} Project",
                description="Test",
                team=self.team,
                deadline=datetime.date.today(),
                status=s
            )
            self.assertEqual(p.status, s)

    def test_project_deleted_on_team_delete(self):
        project = Project.objects.create(
            name="Orphan", description="Will go", team=self.team,
            deadline=datetime.date.today(), status="Active"
        )
        self.team.delete()
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_project_auto_created_at(self):
        project = Project.objects.create(
            name="Auto Time", description="Check timestamps",
            team=self.team, deadline=datetime.date.today(), status="Active"
        )
        self.assertIsNotNone(project.created_at)


class ProjectAPIViewTest(APITestCase):
    """Test cases for ProjectAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.team = Team.objects.create(name="Dev Team", description="Devs")

        self.admin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin123", role="Admin"
        )
        self.manager = User.objects.create_user(
            username="manager", email="manager@test.com", password="pass123",
            role="Manager", team=self.team
        )
        self.member = User.objects.create_user(
            username="member", email="member@test.com", password="pass123",
            role="Member", team=self.team
        )

        self.project = Project.objects.create(
            name="Existing Project",
            description="Already created",
            team=self.team,
            deadline=datetime.date(2025, 12, 31),
            status="Active"
        )

    def _project_data(self, name="Test Project"):
        return {
            "name": name,
            "description": "A test project",
            "team": self.team.id,
            "deadline": "2025-12-31",
            "status": "Active"
        }

    # ─── POST (Create Project) ─────────────────────────────────────────────

    def test_admin_can_create_project(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/projects/", self._project_data("Admin Project"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Admin Project")

    def test_manager_can_create_project(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post("/projects/", self._project_data("Manager Project"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_member_cannot_create_project(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post("/projects/", self._project_data("Member Project"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_project_unauthenticated(self):
        response = self.client.post("/projects/", self._project_data("Ghost Project"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_project_invalid_data(self):
        self.client.force_authenticate(user=self.admin)
        data = {"name": "", "description": "", "team": "", "deadline": "bad-date"}
        response = self.client.post("/projects/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_project_missing_required_fields(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/projects/", {"name": "Incomplete"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_project_invalid_team(self):
        self.client.force_authenticate(user=self.admin)
        data = self._project_data()
        data["team"] = 99999
        response = self.client.post("/projects/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_project_invalid_status(self):
        self.client.force_authenticate(user=self.admin)
        data = self._project_data()
        data["status"] = "InvalidStatus"
        response = self.client.post("/projects/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ─── GET (List / Retrieve) ─────────────────────────────────────────────

    def test_get_all_projects(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_get_single_project_by_id(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get(f"/projects/?id={self.project.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Existing Project")

    def test_get_project_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/projects/?id=99999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_projects_unauthenticated(self):
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ─── PATCH (Partial Update) ────────────────────────────────────────────

    def test_patch_project_success(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/projects/?id={self.project.id}", {"status": "Completed"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "Completed")

    def test_patch_project_without_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch("/projects/", {"status": "Completed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_project_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch("/projects/?id=99999", {"name": "Ghost"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_project_unauthenticated(self):
        response = self.client.patch(
            f"/projects/?id={self.project.id}", {"name": "No Auth"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_project_invalid_deadline(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/projects/?id={self.project.id}", {"deadline": "not-a-date"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ─── DELETE ───────────────────────────────────────────────────────────

    def test_delete_project_success(self):
        extra = Project.objects.create(
            name="Delete Me", description="Temp",
            team=self.team, deadline=datetime.date.today(), status="Active"
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/projects/?id={extra.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Project.objects.filter(id=extra.id).exists())

    def test_delete_project_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete("/projects/?id=99999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_project_without_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete("/projects/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_project_unauthenticated(self):
        response = self.client.delete(f"/projects/?id={self.project.id}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_project_cascades_tasks(self):
        """Deleting a project should cascade-delete its tasks — tested at ORM level"""
        from tasks.models import Task
        task = Task.objects.create(
            title="Task to delete", description="Orphan task",
            project=self.project, priority="High", status="Todo",
            due_date=datetime.date.today()
        )
        project_id = self.project.id
        task_id = task.id
        self.project.delete()
        self.assertFalse(Task.objects.filter(id=task_id).exists())