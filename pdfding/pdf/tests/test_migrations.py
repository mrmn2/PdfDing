import importlib
from pathlib import Path
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth.models import User
from django.core.files import File
from django.db import connection
from django.db.models.functions import Lower
from django.test import TestCase
from pdf.models.pdf_models import Pdf, Tag
from pdf.models.workspace_models import Workspace
from pdf.services.workspace_services import create_workspace
from users.service import get_demo_pdf

add_number_of_pdf_pages = importlib.import_module('pdf.migrations.0009_readd_number_of_pages_with_new_default')
add_pdf_previews = importlib.import_module('pdf.migrations.0013_add_pdf_previews')
add_comments_highlights = importlib.import_module('pdf.migrations.0015_add_comments_highlights')
rename_pdfs_and_add_file_directory = importlib.import_module('pdf.migrations.0016_rename_pdfs_and_add_file_directory')
fill_collections_workspaces = importlib.import_module('pdf.migrations.0020_fill_collections_workspaces')


class TestMigrations(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='12345')
        self.pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_1')

    @patch('pdf.service.PdfProcessingServices.set_thumbnail_and_preview')
    def test_fill_number_of_pages(self, mock_set_thumbnail_and_preview):
        # as I cannot mock the migration file since it has an illegal name and applying the migration
        # in the test did not work either I am using a dummy pdf file -.-. The dummy file has two pages.

        self.assertEqual(self.pdf.number_of_pages, -1)

        dummy_path = Path(__file__).parent / 'data' / 'dummy.pdf'
        with dummy_path.open(mode="rb") as f:
            self.pdf.file = File(f, name=dummy_path.name)
            self.pdf.save()

        add_number_of_pdf_pages.fill_number_of_pages(apps, connection.schema_editor())

        pdf = Pdf.objects.get(id=self.pdf.id)
        self.assertEqual(pdf.number_of_pages, 2)
        # thumbnail cannot be called, otherwise the migration will fail
        mock_set_thumbnail_and_preview.assert_not_called()

    def test_fill_number_of_pages_exception_caught(self):
        self.assertEqual(self.pdf.number_of_pages, -1)
        add_number_of_pdf_pages.fill_number_of_pages(apps, connection.schema_editor())

    def test_fill_thumbnails_and_previews(self):
        # as I cannot mock the migration file since it has an illegal name and applying the migration
        # in the test did not work either I am using a dummy pdf file -.-. The dummy file has two pages.

        self.assertEqual(self.pdf.number_of_pages, -1)
        self.assertFalse(self.pdf.thumbnail)
        self.assertFalse(self.pdf.preview)

        dummy_path = Path(__file__).parent / 'data' / 'dummy.pdf'
        with dummy_path.open(mode="rb") as f:
            self.pdf.file = File(f, name=dummy_path.name)
            self.pdf.save()

        add_pdf_previews.fill_thumbnails_and_previews(apps, connection.schema_editor())

        pdf = Pdf.objects.get(id=self.pdf.id)
        self.assertEqual(pdf.number_of_pages, 2)
        self.assertTrue(pdf.thumbnail)
        self.assertTrue(pdf.preview)

    def test_fill_thumbnails_and_previews_exception_caught(self):
        self.assertEqual(self.pdf.number_of_pages, -1)
        add_pdf_previews.fill_thumbnails_and_previews(apps, connection.schema_editor())

    def test_set_highlights_and_comments(self):
        self.assertFalse(self.pdf.pdfcomment_set.count())
        self.assertFalse(self.pdf.pdfhighlight_set.count())

        self.pdf.file = get_demo_pdf()
        self.pdf.save()

        add_comments_highlights.set_highlights_and_comments(apps, connection.schema_editor())

        pdf = Pdf.objects.get(id=self.pdf.id)
        self.assertTrue(pdf.pdfcomment_set.count())
        self.assertTrue(pdf.pdfhighlight_set.count())

    def test_set_highlights_and_comments_exception_caught(self):
        self.pdf.file = get_demo_pdf()
        self.pdf.save()

        self.assertFalse(self.pdf.pdfcomment_set.count())
        self.assertFalse(self.pdf.pdfhighlight_set.count())
        add_comments_highlights.set_highlights_and_comments(apps, connection.schema_editor())

    def test_rename_pdfs(self):
        # because of the 00xx in the migration file name mocking does not work as expected
        def new_rename_pdf(input_pdf: Pdf):
            input_pdf.file = f'{input_pdf.name}_renamed'
            input_pdf.save()

        orignal_process_renaming_pdf = rename_pdfs_and_add_file_directory.PdfProcessingServices.process_renaming_pdf
        rename_pdfs_and_add_file_directory.PdfProcessingServices.process_renaming_pdf = new_rename_pdf

        for i in range(3):
            Pdf.objects.create(owner=self.user.profile, name=f'rename_{i}', file=f'old_name_{i}')

        rename_pdfs_and_add_file_directory.update_pdf_file_names(apps, connection.schema_editor())

        for pdf in Pdf.objects.filter(name__icontains='rename'):
            self.assertEqual(f'{pdf.name}_renamed', pdf.file.name)

        # undo monkey patching
        rename_pdfs_and_add_file_directory.PdfProcessingServices.process_renaming_pdf = orignal_process_renaming_pdf

    def test_fill_collections_workspaces(self):
        # we need to delete the default user
        self.user.delete()

        user = User.objects.create_user(username='bla', password='12345')

        # we need to delete the personal workspace in order to test the migration
        personal_workspace = user.profile.workspaces[0]
        personal_workspace.delete()

        # create a workspace so we can create pdfs and see if the collection will change with the migration
        created_workspace = create_workspace('dummy', user)
        user.profile.current_workspace_id = created_workspace.id
        user.profile.current_collection_id = 123456
        user.profile.save()

        changed_user = User.objects.get(id=user.id)

        # assert that setup is correct
        self.assertEqual(changed_user.profile.collections.count(), 1)
        self.assertEqual(changed_user.profile.workspaces.count(), 1)
        self.assertEqual(changed_user.profile.current_workspace_id, created_workspace.id)
        self.assertEqual(changed_user.profile.current_collection_id, '123456')

        collection = changed_user.profile.collections[0]
        pdf = Pdf.objects.create(owner=changed_user.profile, name='test', collection=collection)
        tag = Tag.objects.create(owner=changed_user.profile, name='bla', workspace=created_workspace)

        fill_collections_workspaces.fill_data(apps, connection.schema_editor())

        changed_user = User.objects.get(id=user.id)
        changed_pdf = Pdf.objects.get(id=pdf.id)
        changed_tag = Tag.objects.get(id=tag.id)
        profile = changed_user.profile
        workspace = Workspace.objects.get(id=profile.id)

        self.assertEqual(profile.current_collection_id, str(profile.user.id))
        self.assertEqual(profile.current_workspace_id, str(profile.user.id))
        self.assertEqual(profile.workspaces.count(), 2)
        self.assertEqual(profile.collections.count(), 1)
        for ws, expected_name in zip(profile.workspaces.order_by(Lower('name')), ['dummy', 'Personal']):
            self.assertEqual(ws.name, expected_name)
        self.assertEqual(workspace.personal_workspace, True)
        self.assertEqual(workspace.id, str(profile.id))
        self.assertEqual(profile.collections[0].id, str(profile.id))
        self.assertEqual(profile.collections[0].name, 'Default')
        self.assertEqual(profile.collections[0].default_collection, True)
        self.assertEqual(workspace.users.count(), 1)
        self.assertEqual(workspace.owners[0], changed_user)
        self.assertEqual(changed_pdf.collection, profile.collections[0])
        self.assertEqual(changed_tag.workspace, workspace)
