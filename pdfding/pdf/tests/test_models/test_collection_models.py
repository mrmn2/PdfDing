from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models.pdf_models import Pdf


class TestWorkspace(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user_1', password='password')

    def test_pdf_property(self):
        collection = self.user.profile.current_collection
        pdf_1 = Pdf.objects.create(name='pdf_1', collection=collection)
        pdf_2 = Pdf.objects.create(name='pdf_2', collection=collection)
        pdf_3 = Pdf.objects.create(name='pdf_3', collection=collection)

        for collection_pdf, pdf in zip(collection.pdfs.order_by('name'), [pdf_1, pdf_2, pdf_3]):
            self.assertEqual(collection_pdf, pdf)
