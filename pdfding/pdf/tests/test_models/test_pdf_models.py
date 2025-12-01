from datetime import datetime, timedelta
from unittest.mock import patch

from core.settings import MEDIA_ROOT
from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models.pdf_models import (
    Pdf,
    convert_to_natural_age,
    delete_empty_dirs_after_rename_or_delete,
    get_file_path,
    get_pdf_parent_dirs,
    get_preview_path,
    get_thumbnail_path,
)

from pdfding.pdf.services.workspace_services import create_collection, create_workspace


class TestPdf(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.pdf = Pdf(collection=self.user.profile.current_collection, name='pdf')

    # def test_save_delete_pdf_stats(self):
    #     demo_pdf = get_demo_pdf()
    #     user = User.objects.create_user(username='test_user', password='12345')
    #     self.assertEqual(user.profile.number_of_pdfs, 0)
    #     self.assertEqual(user.profile.pdfs_total_size, 0)
    #
    #     pdf_2 = Pdf.objects.create(owner=user.profile, name='pdf_2', file=demo_pdf)
    #     pdf_3 = Pdf.objects.create(owner=user.profile, name='pdf_3', file=demo_pdf)
    #
    #     self.assertEqual(user.profile.number_of_pdfs, 2)
    #     self.assertEqual(user.profile.pdfs_total_size, 2 * 29451)
    #
    #     pdf_2.delete()
    #     self.assertEqual(user.profile.number_of_pdfs, 1)
    #     self.assertEqual(user.profile.pdfs_total_size, 29451)
    #
    #     pdf_3.delete()
    #     self.assertEqual(user.profile.number_of_pdfs, 0)
    #     self.assertEqual(user.profile.pdfs_total_size, 0)

    @patch('pdf.models.pdf_models.delete_empty_dirs_after_rename_or_delete')
    def test_delete(self, mock_delete_empty_dirs_after_rename_or_delete):
        self.pdf.delete()

        self.assertFalse(Pdf.objects.filter(id=self.pdf.id))
        mock_delete_empty_dirs_after_rename_or_delete.assert_not_called()

    @patch('pdf.models.pdf_models.delete_empty_dirs_after_rename_or_delete')
    def test_delete_with_file_directory(self, mock_delete_empty_dirs_after_rename_or_delete):
        file_name = 'test.pdf'
        collection = self.user.profile.current_collection
        pdf = Pdf(collection=collection, name='pdf', file_directory='some/dir')
        pdf.file.name = file_name
        pdf.save()
        pdf.delete()

        self.assertFalse(Pdf.objects.filter(id=pdf.id))
        mock_delete_empty_dirs_after_rename_or_delete.assert_called_once_with(
            file_name, collection.workspace.id, collection.name
        )

    def test_get_pdf_parent_dirs(self):
        ws = create_workspace('bla', self.user)
        ws.id = '12345'
        ws.save()
        collection = create_collection(ws, 'Test')
        pdf = Pdf.objects.create(name='asd', collection=collection)

        expected_parent_dir = '12345/test'

        self.assertEqual(expected_parent_dir, get_pdf_parent_dirs(pdf))

    def test_get_file_path(self):
        collection = self.user.profile.current_collection
        pdf = Pdf(collection=collection, name='PDF_3! 寝る 12/3?  ')

        generated_filepath = get_file_path(pdf, '')

        self.assertEqual(generated_filepath, '1/default/pdf/pdf_3_寝る_12_3.pdf')

    def test_get_file_path_with_sub_dir(self):
        pdf = Pdf(
            collection=self.user.profile.current_collection, name='PDF_3! 寝る 12/3?  ', file_directory='some/sub/dir'
        )

        generated_filepath = get_file_path(pdf, '')

        self.assertEqual(generated_filepath, '1/default/pdf/some/sub/dir/pdf_3_寝る_12_3.pdf')

    def test_get_file_path_empty(self):
        pdf = Pdf(collection=self.user.profile.current_collection, name='!?!?')

        generated_filepath = get_file_path(pdf, '')

        self.assertEqual(generated_filepath, '1/default/pdf/pdf.pdf')

    def test_get_preview_path(self):
        pdf = Pdf(collection=self.user.profile.current_collection, name='PDF_3! 寝る 12/3?  ')

        generated_preview_path = get_preview_path(pdf, '')

        self.assertEqual(generated_preview_path, f'1/default/previews/{pdf.id}.png')

    def test_get_thumbnail_path(self):
        pdf = Pdf(collection=self.user.profile.current_collection, name='PDF_3! 寝る 12/3?  ')

        generated_preview_path = get_thumbnail_path(pdf, '')

        self.assertEqual(generated_preview_path, f'1/default/thumbnails/{pdf.id}.png')

    def test_delete_empty_dirs_after_rename_or_delete_empty(self):
        collection = self.user.profile.current_collection
        workspace_id = collection.workspace.id
        collection_name = collection.name

        sub_dir = 'random/sub/dir'
        sub_dir_paths = [
            MEDIA_ROOT / workspace_id / collection_name.lower() / 'pdf' / directory
            for directory in ['random', 'random/sub', 'random/sub/dir']
        ]

        sub_dir_paths[-1].mkdir(parents=True, exist_ok=True)

        current_file_name = f'{workspace_id}/{collection_name.lower()}/pdf/{sub_dir}/some_file'

        delete_empty_dirs_after_rename_or_delete(current_file_name, workspace_id, collection_name)

        for sub_dir_path in sub_dir_paths:
            self.assertFalse(sub_dir_path.exists())

    def test_delete_empty_dirs_after_rename_or_delete_not_empty(self):
        collection = self.user.profile.current_collection
        workspace_id = collection.workspace.id
        collection_name = collection.name

        sub_dir = 'random/sub/dir'
        sub_dir_paths = [
            MEDIA_ROOT / workspace_id / collection_name.lower() / 'pdf' / directory
            for directory in ['random', 'random/sub', 'random/sub/dir']
        ]
        dummy_file = sub_dir_paths[-2] / 'dummy.txt'

        sub_dir_paths[-1].mkdir(parents=True, exist_ok=True)
        dummy_file.touch()

        current_file_name = f'{workspace_id}/{collection_name.lower()}/pdf/{sub_dir}/some_file'

        delete_empty_dirs_after_rename_or_delete(current_file_name, workspace_id, collection_name)

        # only the 'random/sub/dir' should be deleted the others should remane untouched because of the dummy file
        self.assertFalse(sub_dir_paths[-1].exists())

        for sub_dir_path in sub_dir_paths[:-1]:
            self.assertTrue(sub_dir_path.exists())
        self.assertTrue(dummy_file.exists())

        # cleanup
        dummy_file.unlink()
        for sub_dir_path in sub_dir_paths[:-1:-1]:  # pragma: no cover
            sub_dir_path.rmdir()

    @patch('pdf.models.pdf_models.uuid4', return_value='123456789')
    def test_get_file_path_existing_different_id(self, mock_uuid4):
        pdf_1 = Pdf(collection=self.user.profile.current_collection, name='existing')
        pdf_2 = Pdf(collection=self.user.profile.current_collection, name='exist ing')
        pdf_1.file = '1/default/pdf/exist_ing.pdf'
        pdf_1.save()

        generated_filepath = get_file_path(pdf_2, '')
        self.assertEqual(generated_filepath, '1/default/pdf/exist_ing_12345678.pdf')

    def test_get_file_path_existing_same_id(self):
        pdf = Pdf(collection=self.user.profile.current_collection, name='exist_ing')
        pdf.file = '1/default/pdf/exist_ing.pdf'
        pdf.save()

        generated_filepath = get_file_path(pdf, '')
        self.assertEqual(generated_filepath, '1/default/pdf/exist_ing.pdf')

    def test_natural_age(self):
        self.pdf.creation_date = datetime.now() - timedelta(minutes=5)
        self.assertEqual(convert_to_natural_age(self.pdf.creation_date), '5 minutes')

        self.pdf.creation_date -= timedelta(days=3, hours=2)
        self.assertEqual(convert_to_natural_age(self.pdf.creation_date), '3 days')

    def test_workspace_property(self):
        created_ws = create_workspace('created', self.user)
        created_pdf = Pdf.objects.create(name='bla', collection=created_ws.collections[0])

        self.assertEqual(created_ws, created_pdf.workspace)

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
