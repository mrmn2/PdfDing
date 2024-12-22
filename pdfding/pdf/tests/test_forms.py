from datetime import datetime, timedelta, timezone
from unittest import mock

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
from django.test import Client, TestCase
from pdf import forms
from pdf.forms import CleanHelpers
from pdf.models import Pdf, SharedPdf


class TestPdfForms(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='12345', email='a@a.com')

    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_add_form_valid(self, mock_from_buffer):
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'test1.pdf'
        form = forms.AddForm(data={'name': 'PDF Name'}, owner=self.user.profile, files={'file': file_mock})

        self.assertTrue(form.is_valid())

    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_bulk_add_form_valid(self, mock_from_buffer):
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'test1.pdf'
        form = forms.BulkAddForm(owner=self.user.profile, files={'file': [file_mock]})

        self.assertTrue(form.is_valid())

    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_add_clean_missing_owner(self, mock_from_buffer):
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'test1.pdf'
        form = forms.AddForm(data={'name': 'PDF Name'}, files={'file': file_mock})

        self.assertFalse(form.is_valid())
        # need to test it like this, as owner is not a key of form.errors
        self.assertIn('Owner is missing!', str(form.errors))

    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_bulk_add_clean_missing_owner(self, mock_from_buffer):
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'test1.pdf'
        form = forms.BulkAddForm(files={'file': file_mock})

        self.assertFalse(form.is_valid())
        # need to test it like this, as owner is not a key of form.errors
        self.assertIn('Owner is missing!', str(form.errors))

    @mock.patch('pdf.forms.CleanHelpers.clean_file')
    def test_bulk_add_clean_file(self, mock_clean_file):
        file_mock_1 = mock.MagicMock(spec=File, name='FileMock_1')
        file_mock_1.name = 'test1.pdf'
        file_mock_2 = mock.MagicMock(spec=File, name='FileMock_2')
        file_mock_2.name = 'test2.pdf'
        form = forms.BulkAddForm(files={'file': [file_mock_1, file_mock_2]})

        self.assertFalse(form.is_valid())
        mock_clean_file.assert_has_calls([mock.call(file_mock_1), mock.call(file_mock_2)])

    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_pdf_clean_name_existing(self, mock_from_buffer):
        # create pdf for user
        Pdf.objects.create(owner=self.user.profile, name='existing name')
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'test1.pdf'
        # create the form with the already existing pdf name
        form = forms.AddForm(data={'name': 'existing name'}, owner=self.user.profile, files={'file': file_mock})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['name'], ['A PDF with this name already exists!'])

    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_pdf_clean_name_existing_placeholder(self, mock_from_buffer):
        # create pdf for user
        Pdf.objects.create(owner=self.user.profile, name='bb36974a-3792-47c5-96cc-c79adb87cf82')
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'test1.pdf'
        # create the form with the placeholder name
        form = forms.AddForm(
            data={'name': 'bb36974a-3792-47c5-96cc-c79adb87cf82'}, owner=self.user.profile, files={'file': file_mock}
        )

        self.assertTrue(form.is_valid())


class TestShareForms(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='12345', email='a@a.com')

    def test_add_form_valid(self):
        form = forms.ShareForm(data={'name': 'Share Name'}, owner=self.user.profile)

        self.assertTrue(form.is_valid())

    def test_clean_missing_owner(self):
        form = forms.ShareForm(data={'name': 'Share Name'})

        self.assertFalse(form.is_valid())
        # need to test it like this, as owner is not a key of form.errors
        self.assertIn('Owner is missing!', str(form.errors))

    def test_pdf_clean_name_existing(self):
        # create pdf for user
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_name')
        SharedPdf.objects.create(owner=self.user.profile, pdf=pdf, name='existing name')
        # create the form with the already existing pdf name
        form = forms.ShareForm(data={'name': 'existing name'}, owner=self.user.profile)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['name'], ['A Share with this name already exists!'])

    def test_pdf_clean_name_existing_but_deleted(self):
        deletion_date = datetime.now(timezone.utc) - timedelta(minutes=5)

        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_name')
        SharedPdf.objects.create(owner=self.user.profile, pdf=pdf, name='existing name', deletion_date=deletion_date)
        # create the form with the already existing pdf name
        form = forms.ShareForm(data={'name': 'existing name'}, owner=self.user.profile)

        self.assertTrue(form.is_valid())


class TestViewSharedPasswordForm(TestCase):
    def test_clean_password_input_valid(self):
        user = User.objects.create_user(username='user', password='12345', email='a@a.com')
        pdf = Pdf.objects.create(owner=user.profile, name='pdf_name')
        hashed_password = make_password('password')
        shared_pdf = SharedPdf.objects.create(
            owner=user.profile, pdf=pdf, name='existing name', password=hashed_password
        )

        for password, expected_result in [('password', True), ('wrong_password', False)]:
            form = forms.ViewSharedPasswordForm(data={'password_input': password}, shared_pdf=shared_pdf)

            self.assertEqual(form.is_valid(), expected_result)


class TestTagForms(TestCase):
    @mock.patch('pdf.forms.CleanHelpers.clean_tag_string', return_value='some_name')
    def test_clean_name_valid(self, mock_clean_tag_string):
        # we also test stripping
        for name in ['some_name', ' some_name ']:
            form = forms.TagNameForm(data={'name': name})
            self.assertTrue(form.is_valid())

            mock_clean_tag_string.assert_called_with('some_name')

    def test_clean_name_invalid_spaces(self):
        form = forms.TagNameForm(data={'name': 'spa ces'})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['name'], ['Tag names are not allowed to contain spaces!'])


class TestCleanHelpers(TestCase):
    def test_clean_name(self):
        inputs = ['  this is some    name with whitespaces ', 'simple']
        expected_output = ['this is some name with whitespaces', 'simple']
        generated_output = [forms.CleanHelpers.clean_name(i) for i in inputs]

        self.assertEqual(expected_output, generated_output)

    def test_clean_password_no_password(self):
        self.assertEqual(forms.CleanHelpers.clean_password(''), '')

    def test_clean_password_password(self):
        self.assertEqual(forms.CleanHelpers.clean_password('password'), make_password('password', salt='pdfding'))

    def test_clean_max_views_correct(self):
        self.assertEqual(forms.CleanHelpers.clean_max_views(10), 10)

    def test_clean_max_views_incorrect(self):
        with self.assertRaises(ValidationError):
            forms.CleanHelpers.clean_max_views(-10)

        with self.assertRaises(ValidationError):
            forms.CleanHelpers.clean_max_views(1e10)

    def test_clean_time_input_correct(self):
        self.assertEqual(forms.CleanHelpers.clean_time_input('1d0h22m'), '1d0h22m')

    def test_clean_time_input_incorrect(self):
        with self.assertRaises(ValidationError):
            forms.CleanHelpers.clean_time_input('1d22m')

        with self.assertRaises(ValidationError):
            forms.CleanHelpers.clean_time_input('1:01:22')

    def test_pdf_clean_file_wrong_file_type(self):
        simple_file = SimpleUploadedFile("not_pdf.pdf", b"these are the file contents!")

        with self.assertRaisesMessage(ValidationError, expected_message='Uploaded file is not a PDF!'):
            CleanHelpers.clean_file(simple_file)

    def test_clean_tag_string_correct(self):
        tag_string = 'programming/python/django ot-h_er'

        self.assertEqual(tag_string, CleanHelpers.clean_tag_string(tag_string))

    def test_clean_tag_string_invalid_char(self):
        with self.assertRaisesMessage(
            ValidationError, expected_message='Only letters, numbers, "/", "-" and "_" are valid tag characters!'
        ):
            CleanHelpers.clean_tag_string('inval+id')

    def test_clean_tag_string_starting_ending_slash(self):
        for tag_string in ['tag_1 /tag_2', 'tag/']:
            with self.assertRaisesMessage(ValidationError, expected_message='Tags cannot begin or end with "/"!'):
                CleanHelpers.clean_tag_string(tag_string)

    def test_clean_tag_string_consecutive_slashes(self):
        with self.assertRaisesMessage(
            ValidationError, expected_message='Tags are not allowed to contain consecutive "/" characters!'
        ):
            CleanHelpers.clean_tag_string('inval//id')

    def test_clean_tag_string_multiple_spaces_between(self):
        tag_string = 'programming/python/django   ot-h_er'

        self.assertEqual(tag_string, CleanHelpers.clean_tag_string(tag_string))
