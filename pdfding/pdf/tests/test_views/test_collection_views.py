from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.http import Http404
from django.test import Client, TestCase
from django.urls import reverse
from pdf.forms import CollectionDescriptionForm, CollectionForm, CollectionNameForm
from pdf.services.workspace_services import create_collection, create_workspace
from pdf.views import collection_views


class CollectionTestCase(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username=self.username, password=self.password, email='a@a.com')
        self.client.login(username=self.username, password=self.password)


class TestCollectionMixin(CollectionTestCase):
    def test_get_object(self):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))

        other_collection = create_collection(self.user.profile.current_workspace, 'other')

        assert other_collection == collection_views.CollectionMixin.get_object(
            response.wsgi_request, other_collection.id
        )

    def test_get_object_other_workspace(self):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))

        other_ws = create_workspace('other', self.user)
        other_collection = create_collection(other_ws, 'other')

        with pytest.raises(Http404, match='Given query not found...'):
            collection_views.CollectionMixin.get_object(response.wsgi_request, other_collection.id)


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


class TestEditCollectionMixin(CollectionTestCase):
    def test_get_edit_form_get(self):
        collection = self.user.profile.current_collection
        edit_collection_mixin_object = collection_views.EditCollectionMixin()

        for field, form_class, field_value in zip(
            ['name', 'description'],
            [CollectionNameForm, CollectionDescriptionForm],
            ['Default', 'Default Collection'],
        ):
            form = edit_collection_mixin_object.get_edit_form_get(field, collection)
            self.assertIsInstance(form, form_class)
            self.assertEqual(form.initial, {field: field_value})

    @patch('pdf.views.collection_views.move_collection')
    def test_process_field_name(self, mock_move_collection):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        collection = self.user.profile.current_collection

        collection_views.EditCollectionMixin.process_field(
            'name', collection, response.wsgi_request, {'name': 'new_name'}
        )
        mock_move_collection.assert_called_once_with(collection)

    def test_process_field_name_existing(self):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        request = response.wsgi_request
        collection = self.user.profile.current_collection
        create_collection(self.user.profile.current_workspace, 'existing')

        collection_views.EditCollectionMixin.process_field(
            'name', collection, response.wsgi_request, {'name': 'existing'}
        )

        messages = get_messages(request)

        self.assertEqual(len(messages), 1)
        self.assertEqual(
            list(messages)[0].message, 'This name is already used by another collection in this workspace!'
        )
