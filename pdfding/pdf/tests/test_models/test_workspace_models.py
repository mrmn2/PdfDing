from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models.workspace_models import WorkspaceError, WorkspaceRoles, WorkspaceUser
from pdf.services.workspace_services import create_collection, create_workspace


class TestWorkspace(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user_1', password='password')
        self.ws = create_workspace(name='ws', creator=self.user)

    def test_user_property(self):
        self.assertEqual(self.ws.users.count(), 1)

        user_2 = User.objects.create_user(username='user_2', password='password')
        user_3 = User.objects.create_user(username='user_3', password='password')

        WorkspaceUser.objects.create(workspace=self.ws, user=user_2, role=WorkspaceRoles.ADMIN)
        WorkspaceUser.objects.create(workspace=self.ws, user=user_3, role=WorkspaceRoles.ADMIN)

        self.assertEqual(self.ws.users.count(), 3)

        for expected_user, user in zip([self.user, user_2, user_3], self.ws.users.order_by('username')):
            self.assertEqual(expected_user, user)

    def test_owners_property(self):
        self.assertEqual(self.ws.owners.count(), 1)
        self.assertEqual(self.ws.admins.count(), 0)
        self.assertEqual(self.ws.members.count(), 0)
        self.assertEqual(self.ws.guests.count(), 0)

        user_2 = User.objects.create_user(username='user_2', password='password')
        WorkspaceUser.objects.create(workspace=self.ws, user=user_2, role=WorkspaceRoles.OWNER)

        self.assertEqual(self.ws.owners.count(), 2)
        self.assertEqual(self.ws.admins.count(), 0)
        self.assertEqual(self.ws.members.count(), 0)
        self.assertEqual(self.ws.guests.count(), 0)

        for expected_user, user in zip([self.user, user_2], self.ws.users.order_by('username')):
            self.assertEqual(expected_user, user)

    def test_admins_property(self):
        self.assertEqual(self.ws.owners.count(), 1)
        self.assertEqual(self.ws.admins.count(), 0)
        self.assertEqual(self.ws.members.count(), 0)
        self.assertEqual(self.ws.guests.count(), 0)

        user_2 = User.objects.create_user(username='user_2', password='password')
        WorkspaceUser.objects.create(workspace=self.ws, user=user_2, role=WorkspaceRoles.ADMIN)

        self.assertEqual(self.ws.owners.count(), 1)
        self.assertEqual(self.ws.admins.count(), 1)
        self.assertEqual(self.ws.members.count(), 0)
        self.assertEqual(self.ws.guests.count(), 0)

        self.assertEqual(self.ws.admins[0], user_2)

    def test_members_property(self):
        self.assertEqual(self.ws.owners.count(), 1)
        self.assertEqual(self.ws.admins.count(), 0)
        self.assertEqual(self.ws.members.count(), 0)
        self.assertEqual(self.ws.guests.count(), 0)

        user_2 = User.objects.create_user(username='user_2', password='password')
        WorkspaceUser.objects.create(workspace=self.ws, user=user_2, role=WorkspaceRoles.MEMBER)

        self.assertEqual(self.ws.owners.count(), 1)
        self.assertEqual(self.ws.admins.count(), 0)
        self.assertEqual(self.ws.members.count(), 1)
        self.assertEqual(self.ws.guests.count(), 0)

        self.assertEqual(self.ws.members[0], user_2)

    def test_guests_property(self):
        self.assertEqual(self.ws.owners.count(), 1)
        self.assertEqual(self.ws.admins.count(), 0)
        self.assertEqual(self.ws.members.count(), 0)
        self.assertEqual(self.ws.guests.count(), 0)

        user_2 = User.objects.create_user(username='user_2', password='password')
        WorkspaceUser.objects.create(workspace=self.ws, user=user_2, role=WorkspaceRoles.GUEST)

        self.assertEqual(self.ws.owners.count(), 1)
        self.assertEqual(self.ws.admins.count(), 0)
        self.assertEqual(self.ws.members.count(), 0)
        self.assertEqual(self.ws.guests.count(), 1)

        self.assertEqual(self.ws.guests[0], user_2)

    def test_collections_property(self):
        self.assertEqual(self.ws.collections.count(), 1)

        created_collection = create_collection(self.ws, 'some_collection')

        self.assertEqual(self.ws.collections.count(), 2)

        self.assertEqual(self.ws.collections.order_by('name')[1], created_collection)

    def test_add_workspace_user(self):
        user_2 = User.objects.create_user(username='user_2', password='password')

        self.assertEqual(self.ws.users.count(), 1)
        self.assertEqual(self.ws.admins.count(), 0)

        self.ws.add_user_to_workspace(user_2, WorkspaceRoles.ADMIN)

        self.assertEqual(self.ws.users.count(), 2)
        self.assertEqual(self.ws.admins.count(), 1)
        self.assertEqual(self.ws.admins[0], user_2)

    def test_add_workspace_user_personal_workspace(self):
        personal_ws = self.user.profile.workspaces[0]
        user_2 = User.objects.create_user(username='user_2', password='password')

        with self.assertRaisesMessage(
            WorkspaceError, expected_message='Cannot add other users to personal workspaces!'
        ):
            personal_ws.add_user_to_workspace(user_2, WorkspaceRoles.ADMIN)

    def test_add_workspace_user_user_present(self):
        with self.assertRaisesMessage(WorkspaceError, expected_message='User is already a user of the workspace!'):
            self.ws.add_user_to_workspace(self.user, WorkspaceRoles.ADMIN)
