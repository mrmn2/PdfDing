from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models.workspace_models import WorkspaceRoles
from pdf.services import workspace_services


class TestWorkspaceServices(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='user', password='12345', email='a@a.com')

    def test_create_personal_workspace(self):
        # personal ws with default collection already created
        self.user.profile.workspaces[0].delete()
        self.assertEqual(self.user.profile.workspaces.count(), 0)
        with self.assertRaises(AttributeError):
            self.user.profile.collection

        workspace = workspace_services.create_personal_workspace(self.user)
        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.workspaces.count(), 1)
        self.assertEqual(workspace.name, 'Personal')
        self.assertEqual(workspace.personal_workspace, True)
        print(type(workspace.id))
        self.assertEqual(workspace.id, str(changed_user.id))
        self.assertEqual(workspace.collection_set.count(), 1)
        self.assertEqual(workspace.collection_set.all()[0].id, workspace.id)
        self.assertEqual(workspace.collection_set.all()[0].name, 'Default')
        self.assertEqual(workspace.collection_set.all()[0].default_collection, True)
        self.assertEqual(workspace.workspaceuser_set.count(), 1)
        self.assertEqual(workspace.workspaceuser_set.all()[0].user, changed_user)
        self.assertEqual(workspace.workspaceuser_set.all()[0].role, WorkspaceRoles.OWNER)

    def test_create_workspace(self):
        # personal ws with default collection already created
        self.assertEqual(self.user.profile.workspaces.count(), 1)
        self.assertEqual(self.user.profile.collections.count(), 1)

        workspace = workspace_services.create_workspace('created_ws', self.user)
        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.workspaces.count(), 2)
        self.assertEqual(workspace.name, 'created_ws')
        self.assertEqual(workspace.personal_workspace, False)
        self.assertEqual(workspace.collection_set.count(), 1)
        self.assertEqual(workspace.collection_set.all()[0].id, workspace.id)
        self.assertEqual(workspace.collection_set.all()[0].name, 'Default')
        self.assertEqual(workspace.collection_set.all()[0].default_collection, True)
        self.assertEqual(workspace.workspaceuser_set.count(), 1)
        self.assertEqual(workspace.workspaceuser_set.all()[0].user, changed_user)
        self.assertEqual(workspace.workspaceuser_set.all()[0].role, WorkspaceRoles.OWNER)
