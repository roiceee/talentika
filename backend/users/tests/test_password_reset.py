from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core import mail
from users.models import User, PasswordResetToken


class PasswordResetTestCase(TestCase):
    """Test cases for password reset functionality"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            password="oldpassword123",
        )

    def test_password_reset_request_valid_email(self):
        """Test requesting password reset with valid email"""
        data = {"email": "test@example.com"}
        response = self.client.post("/api/users/password-reset/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("email exists", response.data["message"])

        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Password Reset Request", mail.outbox[0].subject)

    def test_password_reset_request_nonexistent_email(self):
        """Test password reset request with non-existent email (should still return 200)"""
        data = {"email": "nonexistent@example.com"}
        response = self.client.post("/api/users/password-reset/", data)
        # Should return 200 to prevent email enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("email exists", response.data["message"])

        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_request_no_authentication_required(self):
        """Test that password reset does not require authentication"""
        # Make request without authentication
        data = {"email": "test@example.com"}
        response = self.client.post("/api/users/password-reset/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_confirm_valid(self):
        """Test confirming password reset with valid token"""
        # Create reset token
        reset_token = PasswordResetToken.objects.create(user=self.user)

        data = {
            "token": reset_token.token,
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123",
        }
        response = self.client.post("/api/users/password-reset/confirm/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify user can login with new password
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

        # Verify token is marked as used
        reset_token.refresh_from_db()
        self.assertIsNotNone(reset_token.used_at)

    def test_password_reset_confirm_mismatch(self):
        """Test password reset fails with mismatched passwords"""
        reset_token = PasswordResetToken.objects.create(user=self.user)

        data = {
            "token": reset_token.token,
            "new_password": "newpassword123",
            "new_password_confirm": "different123",
        }
        response = self.client.post("/api/users/password-reset/confirm/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_invalid_token(self):
        """Test password reset fails with invalid token"""
        data = {
            "token": "invalid-token-12345",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123",
        }
        response = self.client.post("/api/users/password-reset/confirm/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_expired_token(self):
        """Test password reset fails with expired token"""
        from django.utils import timezone
        from datetime import timedelta

        # Create an expired token
        reset_token = PasswordResetToken.objects.create(user=self.user)
        # Manually set expiration to past
        reset_token.expires_at = timezone.now() - timedelta(hours=1)
        reset_token.save()

        data = {
            "token": reset_token.token,
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123",
        }
        response = self.client.post("/api/users/password-reset/confirm/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", str(response.data).lower())

    def test_password_reset_confirm_used_token(self):
        """Test password reset fails with already used token"""
        reset_token = PasswordResetToken.objects.create(user=self.user)
        reset_token.mark_as_used()

        data = {
            "token": reset_token.token,
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123",
        }
        response = self.client.post("/api/users/password-reset/confirm/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("used", str(response.data).lower())
