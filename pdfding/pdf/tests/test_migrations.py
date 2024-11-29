import importlib
from pathlib import Path

from django.apps import apps
from django.contrib.auth.models import User
from django.core.files import File
from django.db import connection
from django.test import TestCase
from pdf.models import Pdf

add_number_of_pdf_pages = importlib.import_module('pdf.migrations.0007_add_number_of_pdf_pages')


class TestMigrations(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='12345')
        self.pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_1')

    def test_fill_number_of_pages(self):
        # as I cannot mock the migration file since it has an illegal name and applying the migration
        # in the test did not work either I am using a dummy pdf file -.-. The dummy file has two pages.

        self.assertEqual(self.pdf.number_of_pages, 1)

        dummy_path = Path(__file__).parent / 'data' / 'dummy.pdf'
        with dummy_path.open(mode="rb") as f:
            self.pdf.file = File(f, name=dummy_path.name)
            self.pdf.save()

        add_number_of_pdf_pages.fill_number_of_pages(apps, connection.schema_editor())

        pdf = Pdf.objects.get(id=self.pdf.id)
        self.assertEqual(pdf.number_of_pages, 2)

    def test_fill_number_of_pages_exception_caught(self):
        self.assertEqual(self.pdf.number_of_pages, 1)
        add_number_of_pdf_pages.fill_number_of_pages(apps, connection.schema_editor())
