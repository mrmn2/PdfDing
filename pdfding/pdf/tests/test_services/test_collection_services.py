from unittest import mock

from core.settings import MEDIA_ROOT
from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models.pdf_models import Pdf
from pdf.models.shared_pdf_models import SharedPdf
from pdf.services import collection_services


class TestCollectionServices(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='user', password='12345', email='a@a.com')

    @mock.patch('pdf.services.collection_services.adjust_pdf_path')
    @mock.patch('pdf.services.collection_services.move')
    def test_move_collection(self, mock_move, mock_adjust_pdf_path):
        collection = self.user.profile.current_collection
        pdf_1 = Pdf.objects.create(collection=collection, name='pdf_1')
        pdf_2 = Pdf.objects.create(collection=collection, name='pdf_2')
        assert collection.name == 'Default'

        collection.name = 'NEW_name'
        collection_services.move_collection(collection)

        assert collection.name == 'NEW_name'
        mock_move.assert_called_once_with(
            MEDIA_ROOT / collection.workspace.id / 'default', MEDIA_ROOT / collection.workspace.id / 'new_name'
        )
        assert mock_adjust_pdf_path.call_count == 2

        mock_adjust_pdf_path.assert_has_calls(
            [
                mock.call(pdf_1, '/default/', '/new_name/'),
                mock.call(pdf_2, '/default/', '/new_name/'),
            ],
            any_order=True,
        )

    @mock.patch('pdf.services.collection_services.move_collection_file')
    def test_adjust_pdf_path_not_moving(self, mock_move_collection_file):
        collection = self.user.profile.current_collection
        pdf = Pdf.objects.create(collection=collection, name='pdf')
        # make sure only the first occurence is replaced
        pdf.file.name = '1/old/pdf/old/pdf.pdf'
        pdf.preview.name = '1/old/previews/old/pdf'
        pdf.thumbnail.name = '1/old/thumbnails/old/pdf'
        pdf.save()
        shared_pdf = SharedPdf.objects.create(pdf=pdf, name='shared_pdf')
        shared_pdf.file.name = '1/old/qr/old/pdf'
        shared_pdf.save()

        collection_services.adjust_pdf_path(pdf, '/old/', '/new/')
        assert pdf.file.name == '1/new/pdf/old/pdf.pdf'
        assert pdf.thumbnail.name == '1/new/thumbnails/old/pdf'
        assert pdf.preview.name == '1/new/previews/old/pdf'
        # do not ask me why we need to fetch the shared pdf and not the normal one
        changed_shared_pdf = SharedPdf.objects.get(id=shared_pdf.id)
        assert changed_shared_pdf.file.name == '1/new/qr/old/pdf'

        mock_move_collection_file.assert_not_called()

    @mock.patch('pdf.services.collection_services.move_collection_file')
    def test_adjust_pdf_path_moving(self, mock_move_collection_file):
        collection = self.user.profile.current_collection
        pdf = Pdf.objects.create(collection=collection, name='pdf')
        # make sure only the first occurence is replaced
        pdf.file.name = '1/old/pdf/old/pdf.pdf'
        pdf.preview.name = '1/old/previews/old/pdf'
        pdf.thumbnail.name = '1/old/thumbnails/old/pdf'
        pdf.save()
        shared_pdf = SharedPdf.objects.create(pdf=pdf, name='shared_pdf')
        shared_pdf.file.name = '1/old/qr/old/pdf'
        shared_pdf.save()

        collection_services.adjust_pdf_path(pdf, '/old/', '/new/', move_files=True)
        assert pdf.file.name == '1/new/pdf/old/pdf.pdf'
        assert pdf.thumbnail.name == '1/new/thumbnails/old/pdf'
        assert pdf.preview.name == '1/new/previews/old/pdf'
        # do not ask me why we need to fetch the shared pdf and not the normal one
        changed_shared_pdf = SharedPdf.objects.get(id=shared_pdf.id)
        assert changed_shared_pdf.file.name == '1/new/qr/old/pdf'

        assert mock_move_collection_file.call_count == 4

        mock_move_collection_file.assert_has_calls(
            [
                mock.call('1/old/pdf/old/pdf.pdf', '1/new/pdf/old/pdf.pdf'),
                mock.call('1/old/thumbnails/old/pdf', '1/new/thumbnails/old/pdf'),
                mock.call('1/old/previews/old/pdf', '1/new/previews/old/pdf'),
                mock.call('1/old/qr/old/pdf', '1/new/qr/old/pdf'),
            ],
            any_order=True,
        )

    def test_move_collection_file(self):
        old_file_name = '1234/default/pdfs/test.pdf'
        new_file_name = '12345/default/pdfs/test.pdf'
        old_path = MEDIA_ROOT / old_file_name
        new_path = MEDIA_ROOT / new_file_name

        old_path.parent.mkdir(exist_ok=True, parents=True)
        old_path.touch()

        collection_services.move_collection_file(old_file_name, new_file_name)

        assert not old_path.exists()
        assert new_path.exists()
