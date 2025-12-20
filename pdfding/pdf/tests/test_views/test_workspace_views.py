from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from pdf.forms import WorkspaceDescriptionForm, WorkspaceForm, WorkspaceNameForm
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
        self.assertFalse(created_ws.personal_workspace)


class TestWorkspaceMixin(WorkspaceTestCase):
    def test_get_object(self):
        # we need to create a request so get_pdf can access the user profile
        response = self.client.get(reverse('pdf_overview'))

        ws = self.user.profile.current_workspace

        assert ws == workspace_views.WorkspaceMixin.get_object(response.wsgi_request, ws.id)


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
