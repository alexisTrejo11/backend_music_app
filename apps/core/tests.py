from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase


class HealthEndpointTests(TestCase):
    def test_returns_healthy_when_database_is_available(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    @patch("apps.core.views.connection.cursor", side_effect=OperationalError)
    def test_returns_service_unavailable_when_database_is_unavailable(self, mock_cursor):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unhealthy"})
        mock_cursor.assert_called_once_with()


class MetricsEndpointTests(TestCase):
    def test_exposes_prometheus_metrics(self):
        response = self.client.get("/metrics/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response["Content-Type"])
        self.assertIn(b"django_http_requests", response.content)
