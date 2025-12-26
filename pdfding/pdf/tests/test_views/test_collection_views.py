from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from pdf.forms import CollectionForm
from pdf.views import collection_views


class CollectionTestCase(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username=self.username, password=self.password, email='a@a.com')
        self.client.login(username=self.username, password=self.password)


class TestCreateCollectionMixin(CollectionTestCase):
    @patch('pdf.views.collection_views.CreateCollectionMixin.form')
    def test_get_context_get(self, mock_add_form):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))

        create_collection_mixin = collection_views.CreateCollectionMixin()
        generated_context = create_collection_mixin.get_context_get(response.wsgi_request, None)

        mock_add_form.assert_called_once_with(profile=self.user.profile)
        self.assertIsInstance(generated_context['form'], MagicMock)

    def test_obj_save(self):
        self.assertEqual(self.user.profile.current_workspace_id, str(self.user.id))
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        form = CollectionForm(
            data={
                'name': 'some_collection',
                'description': 'some_description',
            },
            profile=self.user.profile,
        )

        collection_views.CreateCollectionMixin.obj_save(form, response.wsgi_request, None)

        changed_user = User.objects.get(id=self.user.id)
        created_collection = changed_user.profile.current_workspace.collections[1]

        self.assertEqual(created_collection.name, 'some_collection')
        self.assertEqual(created_collection.description, 'some_description')
        self.assertFalse(created_collection.default_collection)
