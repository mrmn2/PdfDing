from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse


class TestLoginRequired(TestCase):
    def test_normal_mode(self):
        response = self.client.get(reverse('healthz'))

        self.assertEqual(response.status_code, 200)

    @override_settings(DEMO_MODE=True)
    def test_demo_mode_200(self):
        User.objects.create_user(username='user', password='password', email='a@a.com')
        response = self.client.get(reverse('healthz'))

        self.assertEqual(response.status_code, 200)

    @override_settings(DEMO_MODE=True)
    def test_demo_mode_400_no_user(self):
        response = self.client.get(reverse('healthz'))

        self.assertEqual(response.status_code, 200)

    @override_settings(DEMO_MODE=True)
    def test_demo_mode_400_needs_restart(self):
        user = User.objects.create_user(username='user', password='password', email='a@a.com')
        date_joined_adjusted = datetime.now(timezone.utc) - timedelta(minutes=settings.DEMO_MODE_RESTART_INTERVAL + 1)
        user.date_joined = date_joined_adjusted
        user.save()

        response = self.client.get(reverse('healthz'))
        self.assertEqual(response.status_code, 400)
