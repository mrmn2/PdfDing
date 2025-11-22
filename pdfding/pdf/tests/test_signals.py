from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models.pdf_models import Pdf, Tag
from pdf.models.workspace_models import Workspace, WorkspaceRoles
from pdf.services import workspace_services


class TestSignals(TestCase):
    def test_delete_orphan_tag(self):
        # create pdfs and tags
        user = User.objects.create_user(username='test_user', password='12345')
        pdf_1 = Pdf.objects.create(owner=user.profile, name='pdf_1')
        pdf_2 = Pdf.objects.create(owner=user.profile, name='pdf_2')
        tag_1 = Tag.objects.create(name='tag_1', owner=pdf_1.owner)
        tag_2 = Tag.objects.create(name='tag_2', owner=pdf_2.owner)
        pdf_1.tags.set([tag_1, tag_2])
        pdf_2.tags.set([tag_2])

        pdf_1.delete()

        # check that the tag of pdf 2 was not touched
        pdf_2_tag_names = [tag.name for tag in pdf_2.tags.all()]
        self.assertEqual(pdf_2_tag_names, ['tag_2'])

        # check that tag 1 was deleted
        self.assertFalse(user.profile.tags.filter(name='tag_1').exists())

    @patch('pdf.signals.create_personal_workspace')
    def test_create_workspace(self, mock_create_personal_workspace):
        user = User.objects.create_user(username='test_user', password='12345')

        mock_create_personal_workspace.assert_called_once_with(user)

    def test_handle_workspaces_after_user_delete(self):
        user_1 = User.objects.create_user(username='user_1', password='12345')
        user_2 = User.objects.create_user(username='user_2', password='12345')
        ws_1 = workspace_services.create_workspace('ws_1', user_1)
        ws_2 = workspace_services.create_workspace('ws_2', user_1)
        ws_1.add_user_to_workspace(user_2, WorkspaceRoles.OWNER)
        ws_2.add_user_to_workspace(user_2, WorkspaceRoles.ADMIN)

        user_1.delete()

        self.assertEqual(Workspace.objects.filter(id=ws_1.id).count(), 1)
        self.assertEqual(Workspace.objects.filter(id=ws_2.id).count(), 0)
