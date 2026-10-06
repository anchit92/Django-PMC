from unittest.mock import patch
from django.test import SimpleTestCase, RequestFactory
from django_pmc.views import alb_health_check


class ViewsTestCase(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("django_pmc.views.run_scheduled_tasks")
    def test_alb_health_check_returns_ok_and_spawns_thread(self, mock_run):
        request = self.factory.get("/health/")
        response = alb_health_check(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
