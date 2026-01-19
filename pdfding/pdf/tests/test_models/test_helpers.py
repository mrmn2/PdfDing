from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models.helpers import get_collection_dir
from pdf.models.pdf_models import Pdf
from pdf.services.workspace_services import create_collection, create_workspace


class TestHelpers(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.pdf = Pdf(collection=self.user.profile.current_collection, name='pdf')

    def test_get_collection_dir(self):
        ws = create_workspace('bla', self.user)
        ws.id = '12345'
        ws.save()
        collection = create_collection(ws, 'Test')

        expected_path = '12345/test'

        self.assertEqual(expected_path, get_collection_dir(collection))
