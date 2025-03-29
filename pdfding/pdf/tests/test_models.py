from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pdf.models as models
from core.settings import MEDIA_ROOT
from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models import Pdf, SharedPdf


class TestPdf(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.pdf = models.Pdf(owner=self.user.profile, name='pdf')

    @patch('pdf.models.delete_empty_dirs_after_rename_or_delete')
    def test_delete(self, mock_delete_empty_dirs_after_rename_or_delete):
        self.pdf.delete()

        self.assertFalse(Pdf.objects.filter(id=self.pdf.id))
        mock_delete_empty_dirs_after_rename_or_delete.assert_not_called()

    @patch('pdf.models.delete_empty_dirs_after_rename_or_delete')
    def test_delete_with_file_directory(self, mock_delete_empty_dirs_after_rename_or_delete):
        file_name = 'test.pdf'
        pdf = models.Pdf(owner=self.user.profile, name='pdf', file_directory='some/dir')
        pdf.file.name = file_name
        pdf.save()
        pdf.delete()

        self.assertFalse(Pdf.objects.filter(id=pdf.id))
        mock_delete_empty_dirs_after_rename_or_delete.assert_called_once_with(file_name, self.user.id)

    def test_parse_tag_string(self):
        input_tag_str = '#Tag1  ###tag2      ta&g3 ta+g4'
        expected_tags = ['tag1', 'tag2', 'tag3', 'tag4']
        generated_tags = models.Tag.parse_tag_string(input_tag_str)

        self.assertEqual(expected_tags, generated_tags)

    def test_parse_tag_string_empty(self):
        generated_tags = models.Tag.parse_tag_string('')

        self.assertEqual([], generated_tags)

    def test_get_file_path(self):
        pdf = models.Pdf(owner=self.user.profile, name='PDF_3! 寝る 12/3?  ')

        generated_filepath = models.get_file_path(pdf, '')

        self.assertEqual(generated_filepath, '1/pdf/pdf_3_寝る_12_3.pdf')

    def test_get_file_path_with_sub_dir(self):
        pdf = models.Pdf(owner=self.user.profile, name='PDF_3! 寝る 12/3?  ', file_directory='some/sub/dir')

        generated_filepath = models.get_file_path(pdf, '')

        self.assertEqual(generated_filepath, '1/pdf/some/sub/dir/pdf_3_寝る_12_3.pdf')

    def test_get_file_path_empty(self):
        pdf = models.Pdf(owner=self.user.profile, name='!?!?')

        generated_filepath = models.get_file_path(pdf, '')

        self.assertEqual(generated_filepath, '1/pdf/pdf.pdf')

    def test_delete_empty_dirs_after_rename_or_delete_empty(self):
        user_id = str(self.user.id)

        sub_dir = 'random/sub/dir'
        sub_dir_paths = [
            MEDIA_ROOT / user_id / 'pdf' / directory for directory in ['random', 'random/sub', 'random/sub/dir']
        ]

        sub_dir_paths[-1].mkdir(parents=True, exist_ok=True)

        current_file_name = f'{user_id}/pdf/{sub_dir}/some_file'

        models.delete_empty_dirs_after_rename_or_delete(current_file_name, user_id)

        for sub_dir_path in sub_dir_paths:
            self.assertFalse(sub_dir_path.exists())

    def test_delete_empty_dirs_after_rename_or_delete_not_empty(self):
        user_id = str(self.user.id)

        sub_dir = 'random/sub/dir'
        sub_dir_paths = [
            MEDIA_ROOT / user_id / 'pdf' / directory for directory in ['random', 'random/sub', 'random/sub/dir']
        ]
        dummy_file = sub_dir_paths[-2] / 'dummy.txt'

        sub_dir_paths[-1].mkdir(parents=True, exist_ok=True)
        dummy_file.touch()

        current_file_name = f'{user_id}/pdf/{sub_dir}/some_file'

        models.delete_empty_dirs_after_rename_or_delete(current_file_name, user_id)

        # only the 'random/sub/dir' should be deleted the others should remane untouched because of the dummy file
        self.assertFalse(sub_dir_paths[-1].exists())

        for sub_dir_path in sub_dir_paths[:-1]:
            self.assertTrue(sub_dir_path.exists())
        self.assertTrue(dummy_file.exists())

        # cleanup
        dummy_file.unlink()
        for sub_dir_path in sub_dir_paths[:-1:-1]:  # pragma: no cover
            sub_dir_path.rmdir()

    @patch('pdf.models.uuid4', return_value='123456789')
    def test_get_file_path_existing_different_id(self, mock_uuid4):
        pdf_1 = models.Pdf(owner=self.user.profile, name='existing')
        pdf_2 = models.Pdf(owner=self.user.profile, name='exist ing')
        pdf_1.file = '1/pdf/exist_ing.pdf'
        pdf_1.save()

        generated_filepath = models.get_file_path(pdf_2, '')
        self.assertEqual(generated_filepath, '1/pdf/exist_ing_12345678.pdf')

    def test_get_file_path_existing_same_id(self):
        pdf = models.Pdf(owner=self.user.profile, name='exist_ing')
        pdf.file = '1/pdf/exist_ing.pdf'
        pdf.save()

        generated_filepath = models.get_file_path(pdf, '')
        self.assertEqual(generated_filepath, '1/pdf/exist_ing.pdf')

    def test_get_qrcode_file_path(self):
        generated_filepath = models.get_qrcode_file_path(self.pdf, '')

        self.assertEqual(generated_filepath, f'1/qr/{self.pdf.id}.svg')

    def test_natural_age(self):
        self.pdf.creation_date = datetime.now() - timedelta(minutes=5)
        self.assertEqual(models.convert_to_natural_age(self.pdf.creation_date), '5 minutes')

        self.pdf.creation_date -= timedelta(days=3, hours=2)
        self.assertEqual(models.convert_to_natural_age(self.pdf.creation_date), '3 days')

    def test_progress(self):
        self.pdf.number_of_pages = 1000
        self.pdf.views = 1  # setting this to 1 will cause current_page_for_progress to be equal to current_page
        self.pdf.save()

        for current_page, expected_progress in [(0, 0), (202, 20), (995, 100), (1200, 100)]:
            self.pdf.current_page = current_page
            self.pdf.save()

            self.assertEqual(self.pdf.progress, expected_progress)

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
