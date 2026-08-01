from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from pdf.models.pdf_models import Pdf, Tag
from pdf.models.shared_models import SharedCollection, SharedPdf
from pdf.models.workspace_models import WorkspaceRoles
from pdf.services.pdf_services import get_or_create_pdf_reading_info
from pdf.services.workspace_services import create_collection, create_workspace


class TestViews(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username=self.username, password=self.password, email='a@a.com')
        self.client.login(username=self.username, password=self.password)

    @patch('pdf.services.workspace_services.get_size_of_all_workspace_pdfs', return_value='10.5MB')
    def test_dashboard(self, mock_get_size):
        # we need another ws as users cannot be added to the personal ws
        ws = create_workspace('other_ws', self.user)
        self.user.profile.current_workspace_id = ws.id
        self.user.profile.current_collection_id = ws.id
        self.user.profile.save()

        # create test data
        user_2 = User.objects.create_user(username='other', password='bla', email='other@a.com')
        ws.add_user_to_workspace(user_2, WorkspaceRoles.MEMBER)
        create_collection(ws, 'some_collection')
        create_collection(ws, 'other_collection')
        SharedCollection.objects.create(collection=self.user.profile.current_collection, name='shared_collection')

        pdf_list = []

        for i in range(12):
            pdf = Pdf.objects.create(name=f'pdf_{i}', collection=self.user.profile.current_collection)
            if i > 1:
                tag = Tag.objects.create(name=f'tag_{i}', workspace=self.user.profile.current_workspace)
                pdf.tags.set([tag])
            if i < 3:
                SharedPdf.objects.create(pdf=pdf, name=f'share_{i}')

            # make pdf 0 the most recently viewed pdf
            reading_info = get_or_create_pdf_reading_info(pdf, self.user.profile)
            reading_info.last_viewed_date = datetime.now(timezone.utc) - timedelta(minutes=i)
            reading_info.save()
            pdf_list.append(pdf)

        # test delivered data
        response = self.client.get(reverse('home'))

        self.assertTemplateUsed(response, 'dashboard.html')
        assert response.context['stats_dict'] == {
            'Collections': 3,
            'PDFs': 12,
            'Shared Collections': 1,
            'Shared PDFs': 3,
            'Tags': 10,
            'Total PDF Size': '10.5MB',
            'Users': 2,
        }

        # recently pdfs will ahve size of 10
        recently_viewed_pdfs = response.context['recently_dict']['Recently Viewed']
        recently_added_pdfs = response.context['recently_dict']['Recently Added']

        assert len(recently_viewed_pdfs) == 10
        assert recently_added_pdfs.count() == 10

        for pdf_a, pdf_b in zip(recently_viewed_pdfs, pdf_list[:10]):
            assert pdf_a == pdf_b

        for pdf_a, pdf_b in zip(recently_added_pdfs, reversed(pdf_list[1:])):
            assert pdf_a == pdf_b


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
