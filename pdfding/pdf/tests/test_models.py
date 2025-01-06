from datetime import datetime, timedelta, timezone

import pdf.models as models
from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models import Pdf, SharedPdf


class TestPdf(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.pdf = models.Pdf(owner=self.user.profile, name='pdf')

    def test_parse_tag_string(self):
        input_tag_str = '#Tag1  ###tag2      ta&g3 ta+g4'
        expected_tags = ['tag1', 'tag2', 'tag3', 'tag4']
        generated_tags = models.Tag.parse_tag_string(input_tag_str)

        self.assertEqual(expected_tags, generated_tags)

    def test_parse_tag_string_empty(self):
        generated_tags = models.Tag.parse_tag_string('')

        self.assertEqual([], generated_tags)

    def test_get_file_path(self):
        generated_filepath = models.get_file_path(self.pdf, '')

        self.assertEqual(generated_filepath, f'1/{self.pdf.id}.pdf')

    def test_get_qrcode_file_path(self):
        generated_filepath = models.get_qrcode_file_path(self.pdf, '')

        self.assertEqual(generated_filepath, f'1/qr/{self.pdf.id}.svg')

    def test_natural_age(self):
        self.pdf.creation_date = datetime.now() - timedelta(minutes=5)
        self.assertEqual(self.pdf.natural_age, '5 minutes')

        self.pdf.creation_date -= timedelta(days=3, hours=2)
        self.assertEqual(self.pdf.natural_age, '3 days')

    def test_progress(self):
        self.pdf.number_of_pages = 1000
        self.pdf.views = 1  # setting this to 1 will cause current_page_for_progress to be equal to current_page
        self.pdf.save()

        for current_page, expected_progress in [(0, 0), (202, 20), (995, 100), (1200, 100)]:
            self.pdf.current_page = current_page
            self.pdf.save()

            self.assertEqual(self.pdf.progress, expected_progress)

    def test_file_id(self):
        self.pdf.file.name = f'{self.pdf.owner.user.id}/123456789.pdf'
        self.assertEqual(self.pdf.file_id, '123456789')

    def test_current_page_for_progress(self):
        self.assertEqual(self.pdf.current_page_for_progress, 0)

        self.pdf.views = 1
        self.pdf.save()
        self.assertEqual(self.pdf.current_page_for_progress, 1)

        self.pdf.current_page = -1
        self.pdf.save()
        self.assertEqual(self.pdf.current_page_for_progress, 0)

    def test_notes_html(self):
        self.pdf.notes = '**Code:** `print("PdfDing")`'
        self.assertEqual(self.pdf.notes_html, '<p><strong>Code:</strong> <code>print("PdfDing")</code></p>')

    def test_notes_html_sanitize(self):
        self.pdf.notes = '**Danger:** <script>alert("test")</script>'
        self.assertEqual(self.pdf.notes_html, '<p><strong>Danger:</strong> </p>')


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
