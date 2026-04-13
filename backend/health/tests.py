from rest_framework.test import APITestCase
from rest_framework import status


class HealthCheckTests(APITestCase):
    """Health check endpoint tests"""

    def test_health_check_returns_ok(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")

    def test_health_check_no_auth_required(self):
        """Health endpoint is public — no authentication needed"""
        self.client.credentials()
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
