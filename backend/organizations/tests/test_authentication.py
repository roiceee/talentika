"""
Unit tests for User Authentication and Registration

Tests cover:
- User registration
- JWT authentication with email
- Password validation
- Duplicate email handling
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from users.models import User


class UserRegistrationTests(APITestCase):
    """Test user registration"""

    def test_register_user_success(self):
        """Test successful user registration"""
        url = reverse("register-user")
        data = {
            "email": "testuser@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.data["email"], "testuser@example.com")

    def test_register_user_password_mismatch(self):
        """Test registration fails with password mismatch"""
        url = reverse("register-user")
        data = {
            "email": "testuser@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "SecurePass123!",
            "password_confirm": "DifferentPass123!",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_register_user_duplicate_email(self):
        """Test registration fails with duplicate email"""
        User.objects.create_user(
            email="testuser@example.com",
            username="testuser1",
            password="SecurePass123!",
        )
        url = reverse("register-user")
        data = {
            "email": "testuser@example.com",
            "username": "testuser2",
            "first_name": "Test",
            "last_name": "User",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthenticationTests(APITestCase):
    """Test JWT authentication with email"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            password="SecurePass123!",
        )

    def test_login_with_email(self):
        """Test login using email instead of username"""
        url = reverse("token-obtain")
        data = {"email": "testuser@example.com", "password": "SecurePass123!"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_credentials(self):
        """Test login fails with invalid credentials"""
        url = reverse("token-obtain")
        data = {"email": "testuser@example.com", "password": "WrongPassword"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
