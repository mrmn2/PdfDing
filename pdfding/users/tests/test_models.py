from datetime import datetime, timedelta, timezone

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from pdf.models.collection_models import Collection
from pdf.services.workspace_services import create_workspace


class TestProfile(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='user', password='12345', email='a@a.com')

    # override_settings is not working with this test as the models default value is not overwritten
    # therefore do not change the theme defined in dev.py
    @override_settings(DEFAULT_THEME='dark', DEFAULT_THEME_COLOR='Red')
    def test_default_theme(self):
        user = User.objects.create_user(username='bla', password='12345', email='bla@a.com')

        self.assertEqual(user.profile.dark_mode, 'Dark')
        self.assertEqual(user.profile.theme_color, 'Red')

    def test_dark_mode_str(self):
        self.user.profile.dark_mode = 'Dark'
        self.user.profile.save()

        self.assertEqual(self.user.profile.dark_mode_str, 'dark')

    @override_settings(SUPPORTER_EDITION=True)
    def test_needs_nagging_supporter_edition(self):
        self.user.profile.last_time_nagged = datetime.now(tz=timezone.utc) - timedelta(weeks=9)
        self.user.profile.save()

        self.assertEqual(self.user.profile.needs_nagging, False)

    @override_settings(SUPPORTER_EDITION=False)
    def test_needs_nagging_needed_non_supporter(self):
        self.user.profile.last_time_nagged = datetime.now(tz=timezone.utc) - timedelta(weeks=9)
        self.user.profile.save()

        self.assertEqual(self.user.profile.needs_nagging, True)

    @override_settings(SUPPORTER_EDITION=False)
    def test_needs_nagging_not_needed_non_supporter(self):
        self.user.profile.last_time_nagged = datetime.now(tz=timezone.utc) - timedelta(days=40)
        self.user.profile.save()

        self.assertEqual(self.user.profile.needs_nagging, False)

    def test_pdfs_total_size_with_unit(self):
        profile = self.user.profile
        profile.pdfs_total_size = 10000
        profile.save()

        self.assertEqual(profile.pdfs_total_size_with_unit, '10.0 KB')

        profile.pdfs_total_size = 1234567
        profile.save()

        self.assertEqual(profile.pdfs_total_size_with_unit, '1.23 MB')

        profile.pdfs_total_size = 9.99 * 10**10
        profile.save()

        self.assertEqual(profile.pdfs_total_size_with_unit, '99.9 GB')

        profile.pdfs_total_size = 0
        profile.save()

        self.assertEqual(profile.pdfs_total_size_with_unit, '0.0 KB')

    def test_workspace_property(self):
        user = User.objects.create_user(username='bla', password='12345', email='bla@a.com')
        create_workspace('some_workspace', user)

        self.assertEqual(user.profile.workspaces.count(), 2)

        for workspace, expected_name in zip(user.profile.workspaces.order_by('name'), ['Personal', 'some_workspace']):
            self.assertEqual(workspace.name, expected_name)

    def test_collection_property(self):
        user = User.objects.create_user(username='bla', password='12345', email='bla@a.com')
        self.assertEqual(user.profile.collections.count(), 1)

        workspace = create_workspace('some_workspace', user)
        Collection.objects.create(workspace=workspace, name='some_collection', default_collection=False)
        user.profile.current_workspace_id = workspace.id
        user.profile.save()

        self.assertEqual(user.profile.collections.count(), 2)

        for collection, expected_name in zip(user.profile.collections.order_by('name'), ['Default', 'some_collection']):
            self.assertEqual(collection.name, expected_name)
