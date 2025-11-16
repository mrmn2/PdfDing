from pathlib import Path
from shutil import copy
from unittest import mock

from django.contrib.auth.models import User
from django.core.files import File
from django.test import TestCase, override_settings
from pdf import tasks
from pdf.models.pdf_models import Pdf


class TestTasks(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='username', password='password', email='a@a.com')

    @override_settings(CONSUME_DIR=Path(__file__).parent / 'data' / 'consume')
    @mock.patch('pdf.service.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.service.uuid4', return_value='12345678')
    def test_consume_function(self, mock_uuid4, mock_set_highlights_and_comments):
        # prepare data
        dummy_path = Path(__file__).parent / 'data' / 'dummy.pdf'
        pdf = Pdf.objects.create(owner=self.user.profile, name='dummy_1')
        with dummy_path.open(mode="rb") as f:
            pdf.file = File(f, name=dummy_path.name)
            pdf.save()

        consume_path = Path(__file__).parent / 'data' / 'consume'
        consume_path.mkdir(exist_ok=True)

        user_consume_path = consume_path / str(self.user.id)
        user_consume_path.mkdir(exist_ok=True)

        pdf_path_1 = user_consume_path / 'dummy_1.pdf'
        pdf_path_2 = user_consume_path / 'dummy_2.pdf'
        pdf_path_3 = user_consume_path / 'dummy_3.pdf'
        wrong_pdf_path = consume_path / 'wrong_path.pdf'
        # add a non pdf file. This file should just be ignored
        txt_path = user_consume_path / 'dummy_text.txt'
        txt_path.touch(exist_ok=True)

        for target_path in [pdf_path_1, pdf_path_2, wrong_pdf_path]:
            copy(dummy_path, target_path)

        pdfs = Pdf.objects.filter(owner=self.user.profile).all()
        self.assertEqual(pdfs.count(), 1)

        # test with skip existing set to false
        # consume should create 2 files as we have to valid pdfs dummy_1 and dummy_2
        # as there is already a pdf with the name dummy_1, we expect dummy_1_12345678 as pdf name
        tasks.consume_function(False)

        pdfs = Pdf.objects.filter(owner=self.user.profile).all()
        self.assertEqual(pdfs.count(), 3)
        self.assertEqual(['dummy_1', 'dummy_1_12345678', 'dummy_2'], sorted(pdf.name for pdf in pdfs))
        self.assertEqual(len(list(user_consume_path.iterdir())), 0)

        # test with skip existing set to true
        # only dummy_3 should be created as dummy_1 already exists
        for target_path in [pdf_path_1, pdf_path_3]:
            copy(dummy_path, target_path)

        tasks.consume_function(True)
        pdfs = Pdf.objects.filter(owner=self.user.profile).all()
        self.assertEqual(pdfs.count(), 4)
        self.assertEqual(['dummy_1', 'dummy_1_12345678', 'dummy_2', 'dummy_3'], sorted(pdf.name for pdf in pdfs))
        self.assertEqual(len(list(user_consume_path.iterdir())), 0)

        # check tags are generated and added
        dummy_3 = Pdf.objects.get(name='dummy_3')
        self.assertEqual(sorted(['consumed', 'file']), sorted([tag.name for tag in dummy_3.tags.all()]))

        # test number_of_pages and thumbnail were created
        self.assertEqual(dummy_3.number_of_pages, 2)
        self.assertTrue(dummy_3.thumbnail)

        self.assertEqual(mock_set_highlights_and_comments.call_count, 3)

        # clean up
        wrong_pdf_path.unlink()
        user_consume_path.rmdir()
        consume_path.rmdir()

    def test_passes_consume_condition_fail_not_pdf(self):
        # wrong file type
        self.assertFalse(tasks.passes_consume_condition(Path(__file__), skip_existing=False, pdf_info_list=[]))

        # existing pdf
        dummy_path = Path(__file__).parent / 'data' / 'dummy.pdf'
        pdf_info_list = [('some_pdf', 123456789), ('dummy', 8885)]
        self.assertFalse(tasks.passes_consume_condition(dummy_path, skip_existing=True, pdf_info_list=pdf_info_list))

    def test_consume_condition_fail_not_pdf(self):
        dummy_path = Path(__file__).parent / 'data' / 'dummy.pdf'

        # pdf file, not skipping
        self.assertTrue(tasks.passes_consume_condition(dummy_path, skip_existing=False, pdf_info_list=[]))

        # pdf file, skipping but not existing
        pdf_info_list = [('some_pdf', 123456789), ('other', 8885)]
        self.assertTrue(tasks.passes_consume_condition(dummy_path, skip_existing=True, pdf_info_list=pdf_info_list))
