from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models.helpers import get_collection_path
from pdf.models.pdf_models import Pdf


class TestWorkspace(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user_1', password='password')

    def test_delete(self):
        collection = self.user.profile.current_collection
        collection_path = get_collection_path(collection)
        pdfs_path = collection_path / 'pdf'
        pdfs_path.mkdir(parents=True, exist_ok=True)

        dummy_file_path = pdfs_path / 'dummy.pdf'
        dummy_file_path.touch()

        collection.delete()

        self.assertFalse(collection_path.exists())

    def test_pdf_property(self):
        collection = self.user.profile.current_collection
        pdf_1 = Pdf.objects.create(name='pdf_1', collection=collection)
        pdf_2 = Pdf.objects.create(name='pdf_2', collection=collection)
        pdf_3 = Pdf.objects.create(name='pdf_3', collection=collection)

        for collection_pdf, pdf in zip(collection.pdfs.order_by('name'), [pdf_1, pdf_2, pdf_3]):
            self.assertEqual(collection_pdf, pdf)
