from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from pdf.forms import WorkspaceForm
from pdf.views import workspace_views


def set_up(self):
    self.client = Client()
    self.user = User.objects.create_user(username=self.username, password=self.password, email='a@a.com')
    self.client.login(username=self.username, password=self.password)


class TestCreateWorkspaceMixing(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

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
