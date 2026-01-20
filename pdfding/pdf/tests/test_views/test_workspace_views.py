from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from pdf.forms import WorkspaceDescriptionForm, WorkspaceForm, WorkspaceNameForm
from pdf.models.workspace_models import WorkspaceError
from pdf.services.workspace_services import create_workspace
from pdf.views import workspace_views


class WorkspaceTestCase(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username=self.username, password=self.password, email='a@a.com')
        self.client.login(username=self.username, password=self.password)


class TestCreateWorkspaceMixing(WorkspaceTestCase):
    @patch('pdf.views.workspace_views.CreateWorkspaceMixin.form')
    def test_get_context_get(self, mock_add_form):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))

        create_ws_mixin = workspace_views.CreateWorkspaceMixin()
        generated_context = create_ws_mixin.get_context_get(response.wsgi_request, None)

        mock_add_form.assert_called_once_with(profile=self.user.profile)
        self.assertIsInstance(generated_context['form'], MagicMock)

    def test_obj_save(self):
        self.assertEqual(self.user.profile.current_workspace_id, str(self.user.id))
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        form = WorkspaceForm(
            data={
                'name': 'some_workspace',
                'description': 'some_description',
            },
            profile=self.user.profile,
        )

        workspace_views.CreateWorkspaceMixin.obj_save(form, response.wsgi_request, None)

        changed_user = User.objects.get(id=self.user.id)
        created_ws = changed_user.profile.current_workspace

        self.assertNotEqual(str(self.user.id), changed_user.profile.current_workspace_id)
        self.assertEqual(created_ws.name, 'some_workspace')
        self.assertEqual(created_ws.description, 'some_description')
        self.assertEqual('all', changed_user.profile.current_collection_id)
        self.assertFalse(created_ws.personal_workspace)


class TestWorkspaceMixin(WorkspaceTestCase):
    def test_get_object(self):
        # we need to create a request so get_pdf can access the user profile
        response = self.client.get(reverse('pdf_overview'))

        ws = self.user.profile.current_workspace

        assert ws == workspace_views.WorkspaceMixin.get_object(response.wsgi_request, ws.id)


class TestCollectionDetails(WorkspaceTestCase):
    def test_get(self):
        default_collection = self.user.profile.current_collection

        response = self.client.get(reverse('collection_details', kwargs={'identifier': default_collection.id}))

        self.assertTemplateUsed(response, 'collection_details.html')

        assert response.context['workspace'] == self.user.profile.current_workspace
        assert response.context['collection'] == default_collection
        assert response.context['current_collection_id'] == default_collection.id
        assert response.context['current_collection_name'] == default_collection.name


class TestEditWorkspaceMixin(WorkspaceTestCase):
    def test_get_edit_form_get(self):
        ws = self.user.profile.current_workspace
        edit_workspace_mixin_object = workspace_views.EditWorkspaceMixin()

        for field, form_class, field_value in zip(
            ['name', 'description'],
            [WorkspaceNameForm, WorkspaceDescriptionForm],
            ['Personal', 'Personal Workspace'],
        ):
            form = edit_workspace_mixin_object.get_edit_form_get(field, ws)
            self.assertIsInstance(form, form_class)
            self.assertEqual(form.initial, {field: field_value})


class TestDelete(WorkspaceTestCase):
    def test_delete_get_no_htmx(self):
        created_ws = create_workspace('created_ws', self.user)

        response = self.client.get(reverse('delete_workspace', kwargs={'identifier': created_ws.id}))
        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)

    def test_delete_get(self):
        created_ws = create_workspace('created_ws', self.user)
        headers = {'HTTP_HX-Request': 'true'}

        response = self.client.get(reverse('delete_workspace', kwargs={'identifier': created_ws.id}), **headers)

        self.assertEqual(response.context['workspace_name'], 'created_ws')
        self.assertEqual(response.context['workspace_id'], str(created_ws.id))
        self.assertTemplateUsed(response, 'partials/delete_workspace.html')

    def test_pre_delete(self):
        headers = {'HTTP_HX-Request': 'true'}

        with pytest.raises(WorkspaceError, match='Personal workspaces cannot be deleted!'):
            self.client.delete(
                reverse('delete_workspace', kwargs={'identifier': self.user.profile.current_workspace.id}), **headers
            )

    def test_post_delete_current_ws_adjusted(self):
        created_ws = create_workspace('created_ws', self.user)
        headers = {'HTTP_HX-Request': 'true'}

        profile = self.user.profile
        profile.current_workspace_id = created_ws.id
        profile.current_collection_id = created_ws.id
        profile.save()

        changed_user = User.objects.get(id=self.user.id)
        assert changed_user.profile.current_workspace_id == created_ws.id
        assert changed_user.profile.current_collection_id != 'all'

        self.client.delete(reverse('delete_workspace', kwargs={'identifier': created_ws.id}), **headers)

        changed_user = User.objects.get(id=self.user.id)
        assert changed_user.profile.current_workspace_id == str(changed_user.id)
        assert changed_user.profile.current_collection_id == 'all'
