import importlib
from pathlib import Path

from django.apps import apps
from django.contrib.auth.models import User
from django.core.files import File
from django.db import connection
from django.test import TestCase
from pdf.models import Pdf

add_pdf_overview_layouts = importlib.import_module('users.migrations.0015_add_pdf_overview_layouts')
readd_show_progress_bars = importlib.import_module('users.migrations.0016_readd_show_progress_bars')


class TestMigrations(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='12345')
        self.pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_1')

    def test_fill_adjust_thumbnails_0015(self):
        # as I cannot mock the migration file since it has an illegal name and applying the migration
        # in the test did not work either I am using a dummy pdf file -.-. The dummy file has two pages.

        self.assertEqual(self.pdf.number_of_pages, -1)
        self.assertFalse(self.pdf.thumbnail)
        self.assertFalse(self.pdf.preview)

        dummy_path = Path(__file__).parents[2] / 'pdf' / 'tests' / 'data' / 'dummy.pdf'
        with dummy_path.open(mode="rb") as f:
            self.pdf.file = File(f, name=dummy_path.name)
            self.pdf.save()

        add_pdf_overview_layouts.adjust_thumbnails(apps, connection.schema_editor())

        pdf = Pdf.objects.get(id=self.pdf.id)
        self.assertEqual(pdf.number_of_pages, 2)
        self.assertTrue(pdf.thumbnail)
        self.assertTrue(pdf.preview)

    def test_fill_adjust_thumbnails_0015_exception_caught(self):
        self.assertEqual(self.pdf.number_of_pages, -1)
        add_pdf_overview_layouts.adjust_thumbnails(apps, connection.schema_editor())

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
