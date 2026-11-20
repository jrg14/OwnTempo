from unittest.mock import patch

from django.db import OperationalError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class HealthCheckTests(APITestCase):
    def test_health_check_reports_healthy_services(self):
        response = self.client.get(reverse("health:check"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["checks"]["django"], "ok")
        self.assertEqual(response.data["checks"]["database"], "ok")

    def test_health_check_allows_configured_frontend_origin(self):
        response = self.client.get(
            reverse("health:check"),
            headers={"origin": "http://localhost:5173"},
        )

        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://localhost:5173",
        )

    @patch("apps.health.views.connection.cursor", side_effect=OperationalError)
    def test_health_check_reports_database_failure(self, _mock_cursor):
        response = self.client.get(reverse("health:check"))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "degraded")
        self.assertEqual(response.data["checks"]["database"], "unavailable")

