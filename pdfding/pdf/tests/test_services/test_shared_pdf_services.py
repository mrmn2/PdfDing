from datetime import datetime, timedelta, timezone
from unittest import mock

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.urls import reverse
from pdf.models.pdf_models import Pdf
from pdf.models.shared_pdf_models import SharedPdf
from pdf.services.shared_pdf_services import (
    check_shared_access_allowed,
    check_shared_access_allowed_by_identifier,
    get_future_datetime,
)


class TestSharedPdfServices(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='username', password='password', email='a@a.com')

    def test_check_shared_access_allowed(self):
        # get dummy request
        response = self.client.get(reverse('pdf_overview'))
        request = response.wsgi_request

        # create dummy session
        request.session.create()
        pdf = Pdf.objects.create(name='bla', collection_id=self.user.id)
        shared_pdf = SharedPdf.objects.create(pdf=pdf, name='share')

        assert not check_shared_access_allowed(shared_pdf, request.session)

        shared_pdf.sessions.add(Session.objects.get(session_key=request.session.session_key))
        assert check_shared_access_allowed(shared_pdf, request.session)

        request.session.set_expiry(-1)
        assert not check_shared_access_allowed(shared_pdf, request.session)

    def test_check_shared_access_allowed_inactive(self):
        # get dummy request
        response = self.client.get(reverse('pdf_overview'))
        request = response.wsgi_request

        # create dummy session
        request.session.create()
        pdf = Pdf.objects.create(name='bla', collection_id=self.user.id)

        inactive_shared_pdf = SharedPdf.objects.create(
            pdf=pdf, name='inactive_shared_pdf', expiration_date=(datetime.now(timezone.utc) - timedelta(minutes=5))
        )
        inactive_shared_pdf.sessions.add(Session.objects.get(session_key=request.session.session_key))

        assert not check_shared_access_allowed(inactive_shared_pdf, request.session)

    def test_check_shared_access_allowed_deleted(self):
        # get dummy request
        response = self.client.get(reverse('pdf_overview'))
        request = response.wsgi_request

        # create dummy session
        request.session.create()
        pdf = Pdf.objects.create(name='bla', collection_id=self.user.id)

        deleted_shared_pdf = SharedPdf.objects.create(
            pdf=pdf, name='inactive_shared_pdf', deletion_date=(datetime.now(timezone.utc) - timedelta(minutes=5))
        )
        deleted_shared_pdf.sessions.add(Session.objects.get(session_key=request.session.session_key))

        assert not check_shared_access_allowed(deleted_shared_pdf, request.session)

    @mock.patch('pdf.services.shared_pdf_services.check_shared_access_allowed')
    def test_check_shared_access_allowed_by_identifier(self, mock_check):
        # get dummy request
        response = self.client.get(reverse('pdf_overview'))
        request = response.wsgi_request

        # create dummy session
        request.session.create()
        pdf = Pdf.objects.create(name='bla', collection_id=self.user.id)
        shared_pdf = SharedPdf.objects.create(pdf=pdf, name='share')

        check_shared_access_allowed_by_identifier(shared_pdf.id, request.session)
        mock_check.assert_called_once_with(shared_pdf, request.session)

    def test_get_future_datetime(self):
        expected_result = datetime.now(timezone.utc) + timedelta(days=1, hours=0, minutes=22)
        generated_result = get_future_datetime('1d0h22m')

        self.assertTrue((generated_result - expected_result).total_seconds() < 0.1)

    def test_get_future_datetime_empty(self):
        self.assertEqual(get_future_datetime(''), None)
