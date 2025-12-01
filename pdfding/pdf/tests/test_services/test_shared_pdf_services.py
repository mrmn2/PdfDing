from datetime import datetime, timedelta, timezone

from django.contrib.auth.models import User
from django.test import TestCase
from pdf.services.shared_pdf_services import get_future_datetime


class TestSharedPdfServices(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='username', password='password', email='a@a.com')

    def test_get_future_datetime(self):
        expected_result = datetime.now(timezone.utc) + timedelta(days=1, hours=0, minutes=22)
        generated_result = get_future_datetime('1d0h22m')

        self.assertTrue((generated_result - expected_result).total_seconds() < 0.1)

    def test_get_future_datetime_empty(self):
        self.assertEqual(get_future_datetime(''), None)
