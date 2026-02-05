from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User


class ProfileTestCase(TestCase):
    """Test cases for user profile management"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            password="testpass123",
        )

    def test_get_profile_authenticated(self):
        """Test getting user profile when authenticated"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/users/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["username"], "testuser")

    def test_get_profile_unauthenticated(self):
        """Test getting profile fails when not authenticated"""
        response = self.client.get("/api/users/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_put(self):
        """Test updating profile with PUT"""
        self.client.force_authenticate(user=self.user)
        data = {
            "username": "newusername",
            "first_name": "Updated",
            "last_name": "Name",
        }
        response = self.client.put("/api/users/profile/update/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "newusername")
        self.assertEqual(self.user.first_name, "Updated")

    def test_update_profile_patch(self):
        """Test updating profile with PATCH"""
        self.client.force_authenticate(user=self.user)
        data = {"first_name": "OnlyFirstName"}
        response = self.client.patch("/api/users/profile/update/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "OnlyFirstName")
        self.assertEqual(self.user.username, "testuser")  # Unchanged

    def test_email_readonly(self):
        """Test that email cannot be changed"""
        self.client.force_authenticate(user=self.user)
        original_email = self.user.email
        data = {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "newemail@example.com",  # Should be ignored
        }
        response = self.client.put("/api/users/profile/update/", data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, original_email)
