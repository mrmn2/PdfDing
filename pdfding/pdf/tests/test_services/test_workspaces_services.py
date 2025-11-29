from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from pdf.models.pdf_models import Pdf
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

    def test_create_personal_workspace_exists_already(self):
        with self.assertRaisesMessage(
            WorkspaceError, expected_message='There is already a personal workspace for user a@a.com'
        ):
            workspace_services.create_personal_workspace(self.user)

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

    def test_create_workspace_name_exists(self):
        workspace_services.create_workspace('created_ws', self.user)

        with self.assertRaisesMessage(
            WorkspaceError, expected_message='There is already a workspace named created_ws!'
        ):
            workspace_services.create_workspace('created_ws', self.user)

    def test_create_collection(self):
        ws = self.user.profile.current_workspace

        self.assertEqual(ws.collection_set.count(), 1)

        collection = workspace_services.create_collection(ws, 'Some_collection')

        self.assertEqual(ws.collection_set.count(), 2)
        self.assertEqual(ws.collection_set.order_by('name')[1], collection)

    def test_create_collection_existing_name(self):
        ws = self.user.profile.current_workspace

        workspace_services.create_collection(ws, 'Some_collection')

        with self.assertRaisesMessage(
            WorkspaceError, expected_message='There is already a collection named Some_collection!'
        ):
            workspace_services.create_collection(ws, 'Some_collection')

    def test_get_pdfs_of_workspace(self):
        ws = self.user.profile.current_workspace
        default_collection = self.user.profile.current_collection
        other_collection = workspace_services.create_collection(ws, 'other')

        ws_pdfs = workspace_services.get_pdfs_of_workspace(ws)
        self.assertEqual(ws_pdfs.count(), 0)

        pdf_1 = Pdf.objects.create(name='pdf_1', collection=default_collection)
        pdf_2 = Pdf.objects.create(name='pdf_2', collection=default_collection)
        pdf_3 = Pdf.objects.create(name='pdf_3', collection=other_collection)

        ws_pdfs = workspace_services.get_pdfs_of_workspace(ws)
        self.assertEqual(ws_pdfs.count(), 3)

        for ws_pdf, pdf in zip(ws_pdfs.order_by('name'), [pdf_1, pdf_2, pdf_3]):
            self.assertEqual(ws_pdf, pdf)

    def test_check_if_pdf_with_name_exists(self):
        ws = self.user.profile.current_workspace

        self.assertFalse(workspace_services.check_if_pdf_with_name_exists('dummy', ws))

        Pdf.objects.create(name='dummy', collection=self.user.profile.current_collection)
        self.assertTrue(workspace_services.check_if_pdf_with_name_exists('dummy', ws))
