from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from accounts.models import User
from teams.models import Team


class UserModelTest(TestCase):
    """Test cases for the User model"""

    def setUp(self):
        self.team = Team.objects.create(name="Dev Team", description="Development Team")

    def test_create_user_with_role(self):
        user = User.objects.create_user(
            username="john", email="john@test.com", password="pass123", role="Member"
        )
        self.assertEqual(user.role, "Member")
        self.assertIsNone(user.team)

    def test_create_user_with_team(self):
        user = User.objects.create_user(
            username="jane", email="jane@test.com", password="pass123",
            role="Manager", team=self.team
        )
        self.assertEqual(user.team, self.team)

    def test_user_role_choices(self):
        valid_roles = ["Admin", "Manager", "Member"]
        for role in valid_roles:
            user = User.objects.create_user(
                username=f"user_{role}", email=f"{role}@test.com",
                password="pass123", role=role
            )
            self.assertEqual(user.role, role)

    def test_user_team_set_null_on_team_delete(self):
        user = User.objects.create_user(
            username="bob", email="bob@test.com", password="pass123",
            role="Member", team=self.team
        )
        self.team.delete()
        user.refresh_from_db()
        self.assertIsNone(user.team)


class UserAPIViewTest(APITestCase):
    """Test cases for UserAPIView"""

    def setUp(self):
        self.client = APIClient()
        self.team = Team.objects.create(name="Dev Team", description="Development Team")

        # Admin (superuser)
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin123", role="Admin"
        )
        # Manager
        self.manager = User.objects.create_user(
            username="manager", email="manager@test.com", password="pass123",
            role="Manager", team=self.team
        )
        # Member
        self.member = User.objects.create_user(
            username="member", email="member@test.com", password="pass123",
            role="Member", team=self.team
        )

    # ─── POST (Create User) ────────────────────────────────────────────────

    def test_admin_can_create_user(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "username": "newuser",
            "email": "new@test.com",
            "password": "pass123",
            "role": "Member",
            "team": self.team.id
        }
        response = self.client.post("/auth/register/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "newuser")

    def test_non_admin_cannot_create_user(self):
        self.client.force_authenticate(user=self.manager)
        data = {
            "username": "newuser2",
            "email": "new2@test.com",
            "password": "pass123",
            "role": "Member"
        }
        response = self.client.post("/auth/register/", data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_cannot_create_user(self):
        self.client.force_authenticate(user=self.member)
        data = {
            "username": "newuser3",
            "email": "new3@test.com",
            "password": "pass123",
            "role": "Member"
        }
        response = self.client.post("/auth/register/", data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_with_invalid_data(self):
        self.client.force_authenticate(user=self.admin)
        data = {"username": "", "email": "invalid", "password": ""}
        response = self.client.post("/auth/register/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_unauthenticated(self):
        data = {
            "username": "newuser4",
            "email": "new4@test.com",
            "password": "pass123",
            "role": "Member"
        }
        response = self.client.post("/auth/register/", data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ─── GET (List / Retrieve) ─────────────────────────────────────────────

    def test_get_all_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/auth/register/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_get_single_user_by_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"/auth/register/?id={self.member.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "member")

    def test_get_user_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/auth/register/?id=99999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_users_unauthenticated(self):
        response = self.client.get("/auth/register/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_can_list_users(self):
        """All authenticated users can list — no role restriction on GET"""
        self.client.force_authenticate(user=self.member)
        response = self.client.get("/auth/register/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ─── PATCH (Partial Update) ────────────────────────────────────────────

    def test_patch_user_success(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            "/auth/register/", {"id": self.member.id, "email": "updated@test.com"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "updated@test.com")

    def test_patch_user_without_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            "/auth/register/", {"email": "updated@test.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_user_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            "/auth/register/", {"id": 99999, "email": "x@test.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_user_unauthenticated(self):
        response = self.client.patch(
            "/auth/register/", {"id": self.member.id, "email": "x@test.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ─── DELETE ───────────────────────────────────────────────────────────

    def test_delete_user_success(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f"/auth/register/{self.member.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(id=self.member.id).exists())

    def test_delete_user_not_found(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete("/auth/register/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_user_without_id(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete("/auth/register/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_user_unauthenticated(self):
        response = self.client.delete(f"/auth/register/{self.member.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)