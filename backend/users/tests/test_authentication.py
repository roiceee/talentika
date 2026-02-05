from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User


class AuthenticationTestCase(TestCase):
    """Test cases for user registration and authentication"""

    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        """Test user registration without invitation"""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpass123",
            "password_confirm": "testpass123",
        }
        response = self.client.post("/api/users/auth/register/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_user_login(self):
        """Test user login with email and password"""
        # Create user
        User.objects.create_user(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            password="testpass123",
        )

        # Login
        data = {"email": "test@example.com", "password": "testpass123"}
        response = self.client.post("/api/users/auth/login/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_password_mismatch(self):
        """Test registration fails with password mismatch"""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpass123",
            "password_confirm": "different123",
        }
        response = self.client.post("/api/users/auth/register/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
