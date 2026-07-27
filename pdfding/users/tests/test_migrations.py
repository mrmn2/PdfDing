import importlib
from pathlib import Path

from django.apps import apps
from django.contrib.auth.models import User
from django.core.files import File
from django.db import connection
from django.test import TestCase
from pdf.models.pdf_models import Pdf
from pdf.services.pdf_services import get_or_create_pdf_reading_info
from users.service import get_demo_pdf

readd_show_progress_bars = importlib.import_module('users.migrations.0016_readd_show_progress_bars')
add_pdf_stats = importlib.import_module('users.migrations.0023_add_pdf_stats')
pdf_reading_information_module = importlib.import_module('users.migrations.0032_pdf_reading_info')


class TestMigrations(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='12345')
        self.pdf = Pdf.objects.create(
            name='pdf_1', file=get_demo_pdf(), collection=self.user.profile.current_collection
        )

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

    def test_fill_pdf_reading_information(self):
        pdf_reading_information_module.fill_pdf_reading_info(apps, connection.schema_editor())
        pdf_reading_info = get_or_create_pdf_reading_info(self.pdf, self.user.profile)

        assert pdf_reading_info.pdf == self.pdf
        assert pdf_reading_info.profile == self.user.profile
        assert pdf_reading_info.views == self.pdf.views
        assert pdf_reading_info.current_page == self.pdf.current_page
        assert pdf_reading_info.last_viewed_date == self.pdf.last_viewed_date
