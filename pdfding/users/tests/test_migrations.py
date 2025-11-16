import importlib
from pathlib import Path

from django.apps import apps
from django.contrib.auth.models import User
from django.core.files import File
from django.db import connection
from django.test import TestCase
from pdf.models.pdf_models import Pdf
from users.service import get_demo_pdf

readd_show_progress_bars = importlib.import_module('users.migrations.0016_readd_show_progress_bars')
add_pdf_stats = importlib.import_module('users.migrations.0023_add_pdf_stats')


class TestMigrations(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='12345')
        self.pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_1', file=get_demo_pdf())

    def test_fill_adjust_thumbnails_0016(self):
        # as I cannot mock the migration file since it has an illegal name and applying the migration
        # in the test did not work either I am using a dummy pdf file -.-. The dummy file has two pages.

        self.assertEqual(self.pdf.number_of_pages, -1)
        self.assertFalse(self.pdf.thumbnail)
        self.assertFalse(self.pdf.preview)

        dummy_path = Path(__file__).parents[2] / 'pdf' / 'tests' / 'data' / 'dummy.pdf'
        with dummy_path.open(mode="rb") as f:
            self.pdf.file = File(f, name=dummy_path.name)
            self.pdf.save()

        readd_show_progress_bars.adjust_thumbnails(apps, connection.schema_editor())

        pdf = Pdf.objects.get(id=self.pdf.id)
        self.assertEqual(pdf.number_of_pages, 2)
        self.assertTrue(pdf.thumbnail)
        self.assertTrue(pdf.preview)

    def test_fill_adjust_thumbnails_0016_exception_caught(self):
        self.assertEqual(self.pdf.number_of_pages, -1)
        readd_show_progress_bars.adjust_thumbnails(apps, connection.schema_editor())

    def test_add_pdf_stats_0023(self):
        profile = self.user.profile
        profile.number_of_pdfs = 0
        profile.pdfs_total_size = 0
        profile.save()

        self.assertEqual(self.user.profile.number_of_pdfs, 0)
        self.assertEqual(self.user.profile.pdfs_total_size, 0)

        add_pdf_stats.add_pdf_stats(apps, connection.schema_editor())
        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.number_of_pdfs, 1)
        self.assertEqual(changed_user.profile.pdfs_total_size, 29451)


class TestMigrationServices(TestCase):
    def test_set_pdf_stats(self):
        user = User.objects.create_user(username='user', password="password")
        demo_pdf = get_demo_pdf()
        Pdf.objects.create(owner=user.profile, name='pdf_1', file=demo_pdf)
        Pdf.objects.create(owner=user.profile, name='pdf_2', file=demo_pdf)

        # set everything to zero
        profile = user.profile
        profile.number_of_pdfs = 0
        profile.pdfs_total_size = 0
        profile.save()

        changed_user = User.objects.get(id=user.id)
        self.assertEqual(changed_user.profile.number_of_pdfs, 0)
        self.assertEqual(changed_user.profile.pdfs_total_size, 0)

        add_pdf_stats.set_pdf_stats(changed_user.profile)

        changed_user = User.objects.get(id=user.id)
        self.assertEqual(changed_user.profile.number_of_pdfs, 2)
        self.assertEqual(changed_user.profile.pdfs_total_size, 2 * 29451)

    def test_set_pdf_stats_no_pdfs(self):
        user = User.objects.create_user(username='user', password="password")

        self.assertEqual(user.profile.number_of_pdfs, 0)
        self.assertEqual(user.profile.pdfs_total_size, 0)

        add_pdf_stats.set_pdf_stats(user.profile)

        changed_user = User.objects.get(id=user.id)
        self.assertEqual(changed_user.profile.number_of_pdfs, 0)
        self.assertEqual(changed_user.profile.pdfs_total_size, 0)

    def test_set_pdf_stats_no_file(self):
        user = User.objects.create_user(username='user', password="password")
        Pdf.objects.create(owner=user.profile, name='pdf_1')

        # check that exception is caught as no file is present
        add_pdf_stats.set_pdf_stats(user.profile)
