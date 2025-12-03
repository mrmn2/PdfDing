from datetime import datetime, timedelta, timezone

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from pdf.models.collection_models import Collection
from pdf.models.pdf_models import Pdf
from pdf.models.shared_pdf_models import SharedPdf
from pdf.services.workspace_services import create_collection, create_workspace


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
        create_workspace('some_workspace', self.user)

        self.assertEqual(self.user.profile.workspaces.count(), 2)

        for workspace, expected_name in zip(
            self.user.profile.workspaces.order_by('name'), ['Personal', 'some_workspace']
        ):
            self.assertEqual(workspace.name, expected_name)

    def test_collection_property(self):
        self.assertEqual(self.user.profile.collections.count(), 1)

        workspace = create_workspace('some_workspace', self.user)
        Collection.objects.create(workspace=workspace, name='some_collection', default_collection=False)
        self.user.profile.current_workspace_id = workspace.id
        self.user.profile.save()

        self.assertEqual(self.user.profile.collections.count(), 2)

        for collection, expected_name in zip(
            self.user.profile.collections.order_by('name'), ['Default', 'some_collection']
        ):
            self.assertEqual(collection.name, expected_name)

    def test_pdfs_property(self):
        collection = self.user.profile.current_collection
        other_collection = create_collection(self.user.profile.current_workspace, 'other')

        pdf_1 = Pdf.objects.create(name='pdf_1', collection=collection)
        pdf_2 = Pdf.objects.create(name='pdf_2', collection=collection)
        pdf_3 = Pdf.objects.create(name='pdf_3', collection=other_collection)

        self.assertEqual(self.user.profile.pdfs.count(), 3)

        for pdf_a, pdf_b in zip(self.user.profile.pdfs.order_by('name'), [pdf_1, pdf_2, pdf_3]):
            self.assertEqual(pdf_a, pdf_b)

    def test_shared_pdfs_property(self):
        collection = self.user.profile.current_collection
        other_collection = create_collection(self.user.profile.current_workspace, 'other')

        pdf_1 = Pdf.objects.create(name='pdf_1', collection=collection)
        pdf_2 = Pdf.objects.create(name='pdf_2', collection=other_collection)

        shared_pdf_1 = SharedPdf.objects.create(pdf=pdf_1, name='shared_pdf_1')
        shared_pdf_2 = SharedPdf.objects.create(pdf=pdf_2, name='shared_pdf_2')

        self.assertEqual(self.user.profile.shared_pdfs.count(), 2)

        for shared_pdf_a, shared_pdf_b in zip(
            self.user.profile.shared_pdfs.order_by('name'), [shared_pdf_1, shared_pdf_2]
        ):
            self.assertEqual(shared_pdf_a, shared_pdf_b)

    def test_current_workspace_property(self):
        self.assertEqual(self.user.profile.current_workspace.id, str(self.user.id))

        other_workspace = create_workspace('other_workspace', self.user)
        self.user.profile.current_workspace_id = other_workspace.id
        self.user.profile.save()

        self.assertEqual(self.user.profile.current_workspace, other_workspace)

    def test_current_collection_property(self):
        self.assertEqual(self.user.profile.current_collection.id, str(self.user.id))

        other_collection = create_collection(self.user.profile.current_workspace, 'other')
        self.user.profile.current_collection_id = other_collection.id
        self.user.profile.save()

        self.assertEqual(other_collection, self.user.profile.current_collection)
