from unittest.mock import patch

from admin.views import AdminMixin, OverviewMixin
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class TestLoginRequired(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='non_admin', password='password', email='a@a.com')
        self.user.save()
        self.client = Client()

        self.client.login(username='non_admin', password='password')

    def test_admin_required(self):
        response = self.client.get(reverse('user_overview'))

        self.assertEqual(response.status_code, 404)


class TestOverviewMixin(TestCase):
    def setUp(self):
        admin = User.objects.create_user(username='admin', password='password', email='a@a.com')
        admin.is_superuser = True
        admin.save()

        for i in range(1, 4):
            User.objects.create_user(username=f'user_{i}', password='12345', email=f'{i}_b@a.com')

    def test_filter_objects(self):
        for search_query, expected_result in zip(
            # also use some spaces in the admin search to verify this also works
            ['search=b@a.com&sort=oldest', 'search=@a&tags=admin'],
            [['1_b@a.com', '2_b@a.com', '3_b@a.com'], ['a@a.com']],
        ):
            response = self.client.get(f'{reverse('user_overview')}?{search_query}')
            filtered_users = OverviewMixin.filter_objects(response.wsgi_request)
            user_emails = [user.email for user in filtered_users]

            self.assertEqual(user_emails, expected_result)

    @patch('admin.views.get_latest_version', return_value='0.0.0')
    def test_get_extra_context(self, mock_get_latest_version):
        response = self.client.get(f'{reverse('user_overview')}?search=@a&tags=admin')

        generated_extra_context = OverviewMixin.get_extra_context(response.wsgi_request)
        expected_extra_context = {'search_query': '@a', 'tag_query': ['admin'], 'page': 'user_overview'}

        self.assertEqual(generated_extra_context, expected_extra_context)

    @patch('admin.views.get_latest_version', return_value='0.0.0')
    def test_get_extra_context_empty_queries(self, mock_get_latest_version):
        response = self.client.get(reverse('user_overview'))

        generated_extra_context = OverviewMixin.get_extra_context(response.wsgi_request)
        expected_extra_context = {'search_query': '', 'tag_query': [], 'page': 'user_overview'}

        self.assertEqual(generated_extra_context, expected_extra_context)


class TestAdminMixin(TestCase):
    def test_get_object(self):
        user = User.objects.create_user(username='non_admin', password='password', email='a@a.com')

        self.assertEqual(user, AdminMixin.get_object(None, user.id))


class TestAdminViews(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password', email='a@a.com')
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()
        self.client = Client()

        self.client.login(username='admin', password='password')

    def test_remove_admin_rights(self):
        headers = {'HTTP_HX-Request': 'true'}
        self.client.post(reverse('admin_adjust_rights', kwargs={'identifier': self.user.id}), **headers)

        user = User.objects.get(id=self.user.id)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_add_admin_rights(self):
        user = User.objects.create_user(username='non_admin', password='12345', email='non_admin@a.com')

        headers = {'HTTP_HX-Request': 'true'}
        self.client.post(reverse('admin_adjust_rights', kwargs={'identifier': user.id}), **headers)

        user = User.objects.get(id=user.id)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_adjust_admin_rights_no_htmx(self):
        response = self.client.post(reverse('admin_adjust_rights', kwargs={'identifier': self.user.id}))
        self.assertRedirects(response, reverse('user_overview'), status_code=302)

    @patch('admin.views.get_latest_version', return_value='0.0.0')
    def test_get_information(self, mock_get_latest_version):
        for i in range(1, 4):
            User.objects.create_user(username=f'user_{i}', password='12345', email=f'{i}_b@a.com')

        response = self.client.get(reverse('instance_info'))

        self.assertEqual(response.context['number_of_users'], 4)
        self.assertEqual(response.context['number_of_pdfs'], 0)
        self.assertEqual(response.context['current_version'], 'DEV')
        self.assertEqual(response.context['latest_version'], '0.0.0')
