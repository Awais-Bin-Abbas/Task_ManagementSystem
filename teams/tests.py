from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from accounts.models import User
from teams.models import Team


class TeamModelTest(TestCase):
    """Test cases for Team model"""

    def test_create_team(self):
        team = Team.objects.create(name="Design Team", description="UI/UX designers")
        self.assertEqual(team.name, "Design Team")
        self.assertIsNotNone(team.created_at)

    def test_team_str_fields(self):
        team = Team.objects.create(name="Backend", description="Backend engineers")
        self.assertEqual(team.description, "Backend engineers")

    def test_multiple_teams_created(self):
        Team.objects.create(name="Team A", description="A")
        Team.objects.create(name="Team B", description="B")
        self.assertEqual(Team.objects.count(), 2)


class TeamAPIViewTest(APITestCase):
    """Test cases for TeamAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.team = Team.objects.create(name="Dev Team", description="Developers")

        self.admin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin123", role="Admin"
        )
        self.manager = User.objects.create_user(
            username="manager", email="manager@test.com", password="pass123", role="Manager"
        )
        self.member = User.objects.create_user(
            username="member", email="member@test.com", password="pass123", role="Member"
        )

    # ─── POST (Create Team) ────────────────────────────────────────────────

    def test_admin_can_create_team(self):
        self.client.force_authenticate(user=self.admin)
        data = {"name": "New Team", "description": "A brand new team"}
        response = self.client.post("/teams/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Team")

    def test_manager_can_create_team(self):
        self.client.force_authenticate(user=self.manager)
        data = {"name": "Manager Team", "description": "Created by manager"}
        response = self.client.post("/teams/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_member_cannot_create_team(self):
        self.client.force_authenticate(user=self.member)
        data = {"name": "Member Team", "description": "Should fail"}
        response = self.client.post("/teams/", data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_team_with_invalid_data(self):
        self.client.force_authenticate(user=self.admin)
        data = {"name": "", "description": ""}
        response = self.client.post("/teams/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_team_unauthenticated(self):
        data = {"name": "Ghost Team", "description": "No auth"}
        response = self.client.post("/teams/", data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_team_missing_description(self):
        """Description is a TextField — blank should fail validation"""
        self.client.force_authenticate(user=self.admin)
        data = {"name": "No Desc Team"}
        response = self.client.post("/teams/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ─── GET (List / Retrieve) ─────────────────────────────────────────────

    def test_get_all_teams(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/teams/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_single_team_by_id(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get(f"/teams/?id={self.team.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Dev Team")

    def test_get_team_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/teams/?id=99999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_teams_unauthenticated(self):
        response = self.client.get("/teams/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_can_list_teams(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get("/teams/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ─── PATCH (Partial Update) ────────────────────────────────────────────

    def test_patch_team_success(self):
        self.client.force_authenticate(user=self.admin)
        data = {"id": self.team.id, "name": "Updated Team Name"}
        response = self.client.patch("/teams/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Team Name")

    def test_patch_team_without_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch("/teams/", {"name": "No ID"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_team_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch("/teams/", {"id": 99999, "name": "Ghost"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_team_unauthenticated(self):
        response = self.client.patch("/teams/", {"id": self.team.id, "name": "X"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_team_partial_update_only_description(self):
        self.client.force_authenticate(user=self.manager)
        original_name = self.team.name
        response = self.client.patch("/teams/", {"id": self.team.id, "description": "New desc"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], original_name)
        self.assertEqual(response.data["description"], "New desc")

    # ─── DELETE ───────────────────────────────────────────────────────────

    def test_delete_team_success(self):
        extra_team = Team.objects.create(name="To Delete", description="Temp")
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/teams/{extra_team.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Team.objects.filter(id=extra_team.id).exists())

    def test_delete_team_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete("/teams/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_team_without_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete("/teams/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_team_unauthenticated(self):
        response = self.client.delete(f"/teams/{self.team.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_team_cascades_projects(self):
        """Deleting a team should cascade-delete associated projects"""
        from projects.models import Project
        import datetime
        project = Project.objects.create(
            name="Orphan Project",
            description="Will be deleted",
            team=self.team,
            deadline=datetime.date.today(),
            status="Active"
        )
        # Delete directly via ORM to test the cascade — not via API
        # because the API delete goes through the view which needs the URL param
        team_id = self.team.id
        project_id = project.id
        self.team.delete()
        self.assertFalse(Project.objects.filter(id=project_id).exists())