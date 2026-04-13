"""
Integration tests — Authentication flow

Covers the full sequence:
  Register → Login → Access protected endpoint → Refresh token → Access again
"""

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status


class AuthFlowTests(APITestCase):

    def test_full_auth_flow(self):
        # 1. Register a new user
        register_url = reverse("register")
        register_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = self.client.post(register_url, register_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 2. Login with the new user
        login_url = reverse("login")
        response = self.client.post(
            login_url,
            {"email": "newuser@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        access_token = response.data["access"]
        refresh_token = response.data["refresh"]

        # 3. Access protected endpoint with access token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        profile_url = reverse("user_profile")
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "newuser@example.com")

        # 4. Refresh the token
        self.client.credentials()
        refresh_url = reverse("token_refresh")
        response = self.client.post(
            refresh_url, {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

        new_access_token = response.data["access"]

        # 5. Access protected endpoint with new access token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access_token}")
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_protected_endpoint_rejects_unauthenticated(self):
        profile_url = reverse("user_profile")
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_fails_with_wrong_password(self):
        from users.models import User

        User.objects.create_user(
            email="existing@example.com", username="existing", password="correctpass"
        )
        login_url = reverse("login")
        response = self.client.post(
            login_url,
            {"email": "existing@example.com", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
