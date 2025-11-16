from datetime import datetime, timedelta, timezone

from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models.pdf_models import Pdf
from pdf.models.shared_pdf_models import SharedPdf, get_qrcode_file_path


class TestSharedPdf(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='username', password='password')
        self.pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

    def test_not_inactive(self):
        expiration_date = datetime.now(timezone.utc) + timedelta(minutes=5)

        shared_pdf = SharedPdf.objects.create(
            owner=self.user.profile, pdf=self.pdf, name='share', max_views=5, expiration_date=expiration_date
        )

        self.assertFalse(shared_pdf.inactive)

    def test_inactive_expiration(self):
        expiration_date = datetime.now(timezone.utc) - timedelta(minutes=5)

        shared_pdf = SharedPdf.objects.create(
            owner=self.user.profile, pdf=self.pdf, name='share', max_views=5, expiration_date=expiration_date
        )

        self.assertTrue(shared_pdf.inactive)

    def test_inactive_views(self):
        shared_pdf = SharedPdf.objects.create(owner=self.user.profile, pdf=self.pdf, name='share', max_views=2, views=4)

        self.assertTrue(shared_pdf.inactive)

    def test_deleted(self):
        for minutes, exptected_result in [(5, False), (-5, True)]:
            deletion_date = datetime.now(timezone.utc) + timedelta(minutes=minutes)

            shared_pdf = SharedPdf.objects.create(
                owner=self.user.profile, pdf=self.pdf, name='share', deletion_date=deletion_date
            )

            self.assertEqual(shared_pdf.deleted, exptected_result)

    def test_get_natural_time_future_never(self):
        shared_pdf = SharedPdf.objects.create(owner=self.user.profile, pdf=self.pdf, name='share')
        time_string = shared_pdf.get_natural_time_future(shared_pdf.deletion_date, 'deletes', 'deleted')

        self.assertEqual(time_string, 'deletes never')

    def test_get_natural_time_future_in(self):
        deletion_date = datetime.now(timezone.utc) + timedelta(days=3, hours=2)

        shared_pdf = SharedPdf.objects.create(
            owner=self.user.profile, pdf=self.pdf, name='share', deletion_date=deletion_date
        )
        time_string = shared_pdf.get_natural_time_future(shared_pdf.deletion_date, 'deletes', 'deleted')

        self.assertEqual(time_string, 'deletes in 3 days')

    def test_get_natural_time_future_past(self):
        deletion_date = datetime.now(timezone.utc) - timedelta(days=3, hours=2)

        shared_pdf = SharedPdf.objects.create(
            owner=self.user.profile, pdf=self.pdf, name='share', deletion_date=deletion_date
        )
        time_string = shared_pdf.get_natural_time_future(shared_pdf.deletion_date, 'deletes', 'deleted')

        self.assertEqual(time_string, 'deleted')

    def test_views_string(self):
        shared_pdf = SharedPdf.objects.create(owner=self.user.profile, pdf=self.pdf, name='share', max_views=4, views=2)
        self.assertEqual(shared_pdf.views_string, '2/4 Views')

        shared_pdf = SharedPdf.objects.create(owner=self.user.profile, pdf=self.pdf, name='share', views=2)
        self.assertEqual(shared_pdf.views_string, '2 Views')

    def test_get_qrcode_file_path(self):
        generated_filepath = get_qrcode_file_path(self.pdf, '')

        self.assertEqual(generated_filepath, f'1/qr/{self.pdf.id}.svg')
