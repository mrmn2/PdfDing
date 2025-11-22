from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from pdf.models.workspace_models import WorkspaceError
from pdf.services import workspace_services


class TestWorkspaceServices(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='user', password='12345', email='a@a.com')

    def test_create_personal_workspace(self):
        # personal ws with default collection already created
        self.user.profile.workspaces[0].delete()
        self.assertEqual(self.user.profile.workspaces.count(), 0)
        with self.assertRaises(ObjectDoesNotExist):
            self.user.profile.collections

        workspace = workspace_services.create_personal_workspace(self.user)
        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.workspaces.count(), 1)
        self.assertEqual(workspace.name, 'Personal')
        self.assertEqual(workspace.personal_workspace, True)
        self.assertEqual(workspace.id, str(changed_user.id))
        self.assertEqual(workspace.collections.count(), 1)
        self.assertEqual(workspace.collections[0].id, workspace.id)
        self.assertEqual(workspace.collections[0].name, 'Default')
        self.assertEqual(workspace.collections[0].default_collection, True)
        self.assertEqual(workspace.users.count(), 1)
        self.assertEqual(workspace.owners[0], changed_user)

    def test_create_workspace(self):
        # personal ws with default collection already created
        self.assertEqual(self.user.profile.workspaces.count(), 1)
        self.assertEqual(self.user.profile.collections.count(), 1)

        workspace = workspace_services.create_workspace('created_ws', self.user)
        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.workspaces.count(), 2)
        self.assertEqual(workspace.name, 'created_ws')
        self.assertEqual(workspace.personal_workspace, False)
        self.assertEqual(workspace.collections.count(), 1)
        self.assertEqual(workspace.collections[0].id, workspace.id)
        self.assertEqual(workspace.collections[0].name, 'Default')
        self.assertEqual(workspace.collections[0].default_collection, True)
        self.assertEqual(workspace.users.count(), 1)
        self.assertEqual(workspace.owners[0], changed_user)

    def test_create_collection(self):
        ws = self.user.profile.workspaces[0]

        self.assertEqual(ws.collection_set.count(), 1)

        collection = workspace_services.create_collection(ws, 'Some_collection')

        self.assertEqual(ws.collection_set.count(), 2)
        self.assertEqual(ws.collection_set.order_by('name')[1], collection)

    def test_create_collection_existing_name(self):
        ws = self.user.profile.workspaces[0]

        workspace_services.create_collection(ws, 'Some_collection')

        with self.assertRaisesMessage(
            WorkspaceError, expected_message='There is already a collection named Some_collection!'
        ):
            workspace_services.create_collection(ws, 'Some_collection')
