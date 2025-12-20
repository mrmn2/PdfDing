from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from pdf import forms
from pdf.models.pdf_models import Pdf, PdfComment, PdfHighlight
from pdf.models.tag_models import Tag
from pdf.services.pdf_services import PdfProcessingServices
from pdf.services.workspace_services import create_workspace
from pdf.views import pdf_views
from users.service import get_demo_pdf

DEMO_FILE_SIZE = 29451


def set_up(self):
    self.client = Client()
    self.user = User.objects.create_user(username=self.username, password=self.password, email='a@a.com')
    self.client.login(username=self.username, password=self.password)


class TestAddPDFMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    @patch('pdf.views.pdf_views.forms.AddForm')
    def test_get_context_get(self, mock_add_form):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))

        add_pdf_mixin = pdf_views.AddPdfMixin()
        generated_context = add_pdf_mixin.get_context_get(response.wsgi_request, None)

        mock_add_form.assert_called_once_with(profile=self.user.profile)
        self.assertIsInstance(generated_context['form'], mock.MagicMock)

    @mock.patch('pdf.views.pdf_views.pdf_services.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.pdf_services.PdfProcessingServices.process_with_pypdfium')
    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_obj_save(self, mock_from_buffer, mock_process_with_pypdfium, mock_set_highlights_and_comments):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        form = forms.AddForm(
            data={
                'name': 'some_pdf',
                'tag_string': 'tag_a tag_2',
                'description': 'some_description',
                'notes': 'some_notes',
                'file_directory': 'some/dir',
                'collection': self.user.profile.current_collection.id,
            },
            profile=self.user.profile,
            files={'file': get_demo_pdf()},
        )
        form.is_valid()
        pdf_views.AddPdfMixin.obj_save(form, response.wsgi_request, None)

        pdf = self.user.profile.current_pdfs.get(name='some_pdf')
        tag_names = [tag.name for tag in pdf.tags.all()]
        self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})
        self.assertEqual(pdf.notes, 'some_notes')
        self.assertEqual(pdf.description, 'some_description')
        self.assertEqual(pdf.file_directory, 'some/dir')
        self.assertEqual(pdf.collection, self.user.profile.current_collection)
        self.assertEqual(pdf.file.size, DEMO_FILE_SIZE)
        mock_process_with_pypdfium.assert_called_once_with(pdf)
        mock_set_highlights_and_comments.assert_called_once_with(pdf)

    @mock.patch('pdf.views.pdf_views.pdf_services.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.pdf_services.PdfProcessingServices.process_with_pypdfium')
    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_obj_save_use_file_name(
        self, mock_from_buffer, mock_process_with_pypdfium, mock_set_highlights_and_comments
    ):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        form = forms.AddForm(
            data={
                'name': 'bla',
                'tag_string': 'tag_a tag_2',
                'use_file_name': True,
                'collection': self.user.profile.current_collection.id,
            },
            profile=self.user.profile,
            files={'file': get_demo_pdf()},
        )
        form.is_valid()
        pdf_views.AddPdfMixin.obj_save(form, response.wsgi_request, None)

        pdf = self.user.profile.current_pdfs.get(name='demo')
        tag_names = [tag.name for tag in pdf.tags.all()]
        self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})
        self.assertEqual(pdf.collection, self.user.profile.current_collection)

        mock_process_with_pypdfium.assert_called_once_with(pdf)
        mock_set_highlights_and_comments.assert_called_once_with(pdf)

    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.process_with_pypdfium')
    @override_settings(DEMO_MODE=True)
    def test_obj_save_demo_mode(self, mock_process_with_pypdfium, mock_set_highlights_and_comments):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        form = forms.AddFormNoFile(
            data={
                'name': 'some_pdf',
                'tag_string': 'tag_a tag_2',
                'collection': self.user.profile.current_collection.id,
            },
            profile=self.user.profile,
        )
        form.is_valid()
        pdf_views.AddPdfMixin.obj_save(form, response.wsgi_request, None)

        pdf = self.user.profile.current_collection.pdfs.get(name='some_pdf')
        tag_names = [tag.name for tag in pdf.tags.all()]
        self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})
        self.assertEqual(pdf.file.size, DEMO_FILE_SIZE)
        self.assertEqual(pdf.collection, self.user.profile.current_collection)

        mock_process_with_pypdfium.assert_called_once_with(pdf)
        mock_set_highlights_and_comments.assert_called_once_with(pdf)


class TestBulkAddPDFMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    @patch('pdf.views.pdf_views.forms.BulkAddForm')
    def test_get_context_get(self, mock_add_form):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))

        add_pdf_mixin = pdf_views.BulkAddPdfMixin()
        generated_context = add_pdf_mixin.get_context_get(response.wsgi_request, None)

        mock_add_form.assert_called_once_with(profile=self.user.profile)
        self.assertIsInstance(generated_context['form'], mock.MagicMock)

    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.process_with_pypdfium')
    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_obj_save_single_file_no_skipping(
        self, mock_from_buffer, mock_process_with_pypdfium, mock_set_highlights_and_comments
    ):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        form = forms.BulkAddForm(
            data={
                'tag_string': 'tag_a tag_2',
                'description': '',
                'file_directory': 'some/dir',
                'collection': self.user.profile.current_collection.id,
            },
            profile=self.user.profile,
            files=MultiValueDict({'file': [get_demo_pdf()]}),
        )

        pdf_views.BulkAddPdfMixin.obj_save(form, response.wsgi_request, None)

        pdf = self.user.profile.current_collection.pdfs.get(name='demo')
        tag_names = [tag.name for tag in pdf.tags.all()]
        self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})
        self.assertEqual(pdf.collection, self.user.profile.current_collection)
        self.assertEqual(pdf.file_directory, 'some/dir')
        self.assertEqual(pdf.file.size, DEMO_FILE_SIZE)
        mock_process_with_pypdfium.assert_called_once_with(pdf)
        mock_set_highlights_and_comments.assert_called_once_with(pdf)

    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.process_with_pypdfium')
    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_obj_save_multiple_files_no_skipping(
        self, mock_from_buffer, mock_process_with_pypdfium, mock_set_highlights_and_comments
    ):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))

        file_1 = get_demo_pdf()
        file_2 = get_demo_pdf()
        file_2.name = 'demo_2'

        form = forms.BulkAddForm(
            data={
                'tag_string': 'tag_a tag_2',
                'description': 'some_description',
                'notes': 'some_notes',
                'collection': self.user.profile.current_collection.id,
            },
            profile=self.user.profile,
            files=MultiValueDict({'file': [file_1, file_2]}),
        )

        pdf_views.BulkAddPdfMixin.obj_save(form, response.wsgi_request, None)

        for name in ['demo', 'demo_2']:
            pdf = self.user.profile.current_pdfs.get(name=name)
            tag_names = [tag.name for tag in pdf.tags.all()]
            self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})
            self.assertEqual(pdf.description, 'some_description')
            self.assertEqual(pdf.notes, 'some_notes')
            self.assertEqual(pdf.collection, self.user.profile.current_collection)
            # check that pdf pages are set to -1 in case of exception.
            # in this test there should be an exception as a mock file is used.
            self.assertEqual(pdf.number_of_pages, -1)

    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.process_with_pypdfium')
    @mock.patch('pdf.services.pdf_services.uuid4', return_value='123456789')
    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_obj_save_multiple_files_skipping(
        self, mock_from_buffer, mock_uuid4, mock_process_with_pypdfium, mock_set_highlights_and_comments
    ):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))

        # create pdfs test1 and test2
        old_pdfs = []
        for i in range(1, 3):
            file_contents = bytes('contents' * i, encoding='utf-8')
            simple_file = SimpleUploadedFile(f'test{i}.pdf', file_contents)
            old_pdf = Pdf.objects.create(
                collection=self.user.profile.current_collection, name=f'test{i}', file=simple_file
            )
            old_pdfs.append(old_pdf)

        files = []

        # file1: same name and size -> should not be created
        # file2: same name, different size -> should be created with different name
        # file3: different name, same size -> should be created with original name
        for i in range(1, 4):
            file_contents = bytes('contents', encoding='utf-8')
            simple_file = SimpleUploadedFile(f'test{i}.pdf', file_contents)
            files.append(simple_file)

        form = forms.BulkAddForm(
            data={
                'tag_string': 'tag_a tag_2',
                'description': 'description',
                'skip_existing': 'on',
                'collection': self.user.profile.current_collection.id,
            },
            profile=self.user.profile,
            files=MultiValueDict({'file': files}),
        )

        pdf_views.BulkAddPdfMixin.obj_save(form, response.wsgi_request, None)

        expected_pdf_names = ['test1', 'test2', 'test2_12345678', 'test3']
        generated_pdf_names = [pdf.name for pdf in self.user.profile.current_pdfs]
        self.assertEqual(expected_pdf_names, generated_pdf_names)

        # also check date the test1 and test2 are unchanged
        for i in range(2):
            self.assertEqual(old_pdfs[i], self.user.profile.current_pdfs.get(name=f'test{i + 1}'))

    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.process_with_pypdfium')
    @override_settings(DEMO_MODE=True)
    def test_obj_save_demo_mode(self, mock_process_with_pypdfium, mock_set_highlights_and_comments):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        form = forms.BulkAddFormNoFile(
            data={
                'tag_string': 'tag_a tag_2',
                'description': 'description',
                'collection': self.user.profile.current_collection.id,
            },
            profile=self.user.profile,
        )

        pdf_views.BulkAddPdfMixin.obj_save(form, response.wsgi_request, None)

        pdf = self.user.profile.current_pdfs.get(name='demo')
        tag_names = [tag.name for tag in pdf.tags.all()]
        self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})
        self.assertEqual('description', 'description')
        self.assertEqual(pdf.collection, self.user.profile.current_collection)
        self.assertEqual(pdf.file.size, DEMO_FILE_SIZE)

        mock_process_with_pypdfium.assert_called_once_with(pdf)
        mock_set_highlights_and_comments.assert_called_once_with(pdf)


class TestOverviewMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    def test_filter_objects(self):
        # create some pdfs
        for i in range(1, 15):
            pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name=f'pdf_{i % 5}_{i}')

            # add a tag to pdf 2, 7
            if i % 5 == 2 and i < 10:
                tag = Tag.objects.create(name=f'tag_{i}', workspace=self.user.profile.current_workspace)
                pdf.tags.set([tag])

        pdf_1 = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf_to_be_found_1')
        pdf_2 = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf_to_be_found_2')
        pdf_3 = Pdf.objects.create(collection=self.user.profile.current_collection, name='not_to_be_found')
        tags = []

        for name in ['programming', 'programming/python', 'programming/python/django', 'programming/python/flask']:
            tag = Tag.objects.create(name=name, workspace=self.user.profile.current_workspace)
            tags.append(tag)

        pdf_1.tags.set(tags)
        pdf_2.tags.set(tags[2:3])
        pdf_3.tags.set(tags)

        response = self.client.get(f'{reverse('pdf_overview')}?search=pdf_&tags=programming/python')

        filtered_pdfs = pdf_views.OverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(sorted(list(filtered_pdfs), key=lambda a: a.name), [pdf_1, pdf_2])

    def test_filter_objects_starred(self):
        pdf_1 = Pdf.objects.create(
            collection=self.user.profile.current_collection, name='pdf_to_be_found_1', starred=True
        )
        pdf_2 = Pdf.objects.create(
            collection=self.user.profile.current_collection, name='pdf_to_be_found_2', starred=True
        )
        Pdf.objects.create(collection=self.user.profile.current_collection, name='not_to_be_found')

        response = self.client.get(f'{reverse('pdf_overview')}?selection=starred')

        filtered_pdfs = pdf_views.OverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(sorted(list(filtered_pdfs), key=lambda a: a.name), [pdf_1, pdf_2])

    def test_filter_objects_ignore_not_current(self):
        pdf_1 = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf_to_be_found_1')
        pdf_2 = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf_to_be_found_2')

        other_ws = create_workspace('other_ws', creator=self.user)
        Pdf.objects.create(collection=other_ws.collections[0], name='pdf_not_to_be_found')

        response = self.client.get(reverse('pdf_overview'))

        filtered_pdfs = pdf_views.OverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(filtered_pdfs.count(), 2)
        self.assertEqual(sorted(list(filtered_pdfs), key=lambda a: a.name), [pdf_1, pdf_2])

    def test_filter_objects_ignore_archived(self):
        pdf_1 = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf_to_be_found_1')
        pdf_2 = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf_to_be_found_2')
        Pdf.objects.create(collection=self.user.profile.current_collection, name='not_to_be_found', archived=True)

        response = self.client.get(f'{reverse('pdf_overview')}')

        filtered_pdfs = pdf_views.OverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(sorted(list(filtered_pdfs), key=lambda a: a.name), [pdf_1, pdf_2])

    def test_filter_objects_archived(self):
        pdf_1 = Pdf.objects.create(
            collection=self.user.profile.current_collection, name='pdf_to_be_found_1', archived=True
        )
        Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf_to_be_found_2')
        Pdf.objects.create(collection=self.user.profile.current_collection, name='not_to_be_found')

        response = self.client.get(f'{reverse('pdf_overview')}?selection=archived')

        filtered_pdfs = pdf_views.OverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(list(filtered_pdfs), [pdf_1])

    def test_fuzzy_filter_pdfs(self):
        Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf_not_to_be_found')
        pdf_self_hosted = Pdf.objects.create(
            collection=self.user.profile.current_collection, name='The best self-hosted applications '
        )
        pdf_self_hosting = Pdf.objects.create(
            collection=self.user.profile.current_collection, name='Self-hosting Guide'
        )
        Pdf.objects.create(collection=self.user.profile.current_collection, name='self sufficiency')

        filtered_pdfs = pdf_views.OverviewMixin.fuzzy_filter_pdfs(Pdf.objects.all(), 'self hosted')
        self.assertEqual(sorted(list(filtered_pdfs), key=lambda a: a.name), [pdf_self_hosting, pdf_self_hosted])

    @override_settings(SUPPORTER_EDITION=True)
    @patch('pdf.services.tag_services.TagServices.get_tag_info_dict', return_value='tag_info_dict')
    def test_get_extra_context(self, mock_get_tag_info_dict):
        response = self.client.get(f'{reverse('pdf_overview')}?search=searching&tags=tagging')

        generated_extra_context = pdf_views.OverviewMixin.get_extra_context(response.wsgi_request)
        expected_extra_context = {
            'search_query': 'searching',
            'tag_query': ['tagging'],
            'tag_info_dict': 'tag_info_dict',
            'special_pdf_selection': '',
            'page': 'pdf_overview',
            'layout': 'Compact',
            'needs_nagging': False,
        }

        self.assertEqual(generated_extra_context, expected_extra_context)

    @override_settings(SUPPORTER_EDITION=True)
    @patch('pdf.services.tag_services.TagServices.get_tag_info_dict', return_value='tag_info_dict')
    def test_get_extra_context_selection(self, mock_get_tag_info_dict):
        response = self.client.get(f'{reverse('pdf_overview')}?selection=starred')

        generated_extra_context = pdf_views.OverviewMixin.get_extra_context(response.wsgi_request)
        expected_extra_context = {
            'search_query': '',
            'tag_query': [],
            'tag_info_dict': 'tag_info_dict',
            'special_pdf_selection': 'starred',
            'page': 'pdf_overview_starred',
            'layout': 'Compact',
            'needs_nagging': False,
        }

        self.assertEqual(generated_extra_context, expected_extra_context)

    @override_settings(SUPPORTER_EDITION=True)
    @patch('pdf.services.tag_services.TagServices.get_tag_info_dict', return_value='tag_info_dict')
    def test_get_extra_context_selection_invalid(self, mock_get_tag_info_dict):
        response = self.client.get(f'{reverse('pdf_overview')}?selection=invalid')

        generated_extra_context = pdf_views.OverviewMixin.get_extra_context(response.wsgi_request)
        expected_extra_context = {
            'search_query': '',
            'tag_query': [],
            'tag_info_dict': 'tag_info_dict',
            'special_pdf_selection': '',
            'page': 'pdf_overview',
            'layout': 'Compact',
            'needs_nagging': False,
        }

        self.assertEqual(generated_extra_context, expected_extra_context)

    @override_settings(SUPPORTER_EDITION=True)
    @patch('pdf.services.tag_services.TagServices.get_tag_info_dict', return_value='tag_info_dict')
    def test_get_extra_context_empty_queries(self, mock_get_tag_info_dict):
        response = self.client.get(reverse('pdf_overview'))

        generated_extra_context = pdf_views.OverviewMixin.get_extra_context(response.wsgi_request)
        expected_extra_context = {
            'search_query': '',
            'tag_query': [],
            'tag_info_dict': 'tag_info_dict',
            'special_pdf_selection': '',
            'page': 'pdf_overview',
            'layout': 'Compact',
            'needs_nagging': False,
        }

        self.assertEqual(generated_extra_context, expected_extra_context)

    @override_settings(SUPPORTER_EDITION=False)
    def test_do_extra_action_reset(self):
        self.user.profile.last_time_nagged = datetime.now(tz=timezone.utc) - timedelta(weeks=9)
        self.user.profile.save()

        self.assertTrue(self.user.profile.needs_nagging)

        self.client.get(reverse('pdf_overview'))

        changed_user = User.objects.get(id=self.user.id)

        self.assertFalse(changed_user.profile.needs_nagging)
        self.assertTrue((changed_user.profile.last_time_nagged - datetime.now(tz=timezone.utc)) < timedelta(minutes=1))

    @override_settings(SUPPORTER_EDITION=False)
    def test_do_extra_action_no_reset(self):
        current_datetime = datetime.now(tz=timezone.utc) - timedelta(weeks=6)
        self.user.profile.last_time_nagged = current_datetime
        self.user.profile.save()

        self.assertFalse(self.user.profile.needs_nagging)

        self.client.get(reverse('pdf_overview'))

        changed_user = User.objects.get(id=self.user.id)

        self.assertFalse(changed_user.profile.needs_nagging)
        self.assertEqual(changed_user.profile.last_time_nagged, current_datetime)


class TestPdfMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    def test_get_object(self):
        # make sure we can access pdf of not active ws
        other_ws = create_workspace('other_ws', creator=self.user)
        pdf = Pdf.objects.create(collection=other_ws.collections[0], name='pdf')

        self.assertNotEqual(other_ws, self.user.profile.current_workspace)

        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        pdf_retrieved = pdf_views.PdfMixin.get_object(response.wsgi_request, pdf.id)

        self.assertEqual(pdf, pdf_retrieved)


class TestEditPdfMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    def test_get_edit_form_get(self):
        pdf = Pdf.objects.create(
            collection=self.user.profile.current_collection,
            name='pdf_name',
            description='some_description',
            notes='some_note',
        )
        tags = [Tag.objects.create(name=f'tag_{i}', workspace=self.user.profile.current_workspace) for i in range(2)]
        pdf.tags.set(tags)

        edit_pdf_mixin_object = pdf_views.EditPdfMixin()

        for field, form_class, field_value in zip(
            ['name', 'description', 'tags', 'notes'],
            [forms.NameForm, forms.DescriptionForm, forms.PdfTagsForm, forms.NotesForm],
            ['pdf_name', 'some_description', 'tag_0 tag_1', 'some_note'],
        ):
            form = edit_pdf_mixin_object.get_edit_form_get(field, pdf)
            self.assertIsInstance(form, form_class)
            if field == 'tags':
                field = 'tag_string'
            self.assertEqual(form.initial, {field: field_value})

    def test_process_field_tag(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf', description='something')
        tag_1 = Tag.objects.create(name='tag_1', workspace=self.user.profile.current_workspace)
        tag_2 = Tag.objects.create(name='tag_2', workspace=self.user.profile.current_workspace)

        pdf.tags.set([tag_1, tag_2])

        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        pdf_views.EditPdfMixin.process_field('tags', pdf, response.wsgi_request, {'tag_string': 'tag_1 tag_3'})

        # get pdf again with the changes
        pdf = self.user.profile.current_pdfs.get(id=pdf.id)
        tag_names = [tag.name for tag in pdf.tags.all()]

        self.assertEqual(sorted(tag_names), sorted(['tag_1', 'tag_3']))
        # check that tag 2 was deleted
        self.assertFalse(self.user.profile.tags.filter(name='tag_2').exists())

    @patch('pdf.views.pdf_views.PdfProcessingServices.process_renaming_pdf')
    def test_process_field_name(self, mock_process_renaming_pdf):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')
        request = response.wsgi_request

        pdf_views.EditPdfMixin.process_field('name', pdf, request, {'name': 'new_name'})
        mock_process_renaming_pdf.assert_called_once_with(pdf)

    def test_process_field_name_existing(self):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')
        pdf_2 = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf_2')
        request = response.wsgi_request

        pdf_views.EditPdfMixin.process_field('name', pdf, request, {'name': pdf_2.name})

        messages = get_messages(request)

        self.assertEqual(len(messages), 1)
        self.assertEqual(list(messages)[0].message, 'This name is already used by another PDF!')

    @patch('pdf.views.pdf_views.PdfProcessingServices.process_renaming_pdf')
    def test_process_field_file_directory(self, mock_process_renaming_pdf):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')
        request = response.wsgi_request

        pdf_views.EditPdfMixin.process_field('file_directory', pdf, request, {'file_directory': 'some/dir'})
        mock_process_renaming_pdf.assert_called_once_with(pdf)


class TestViews(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    @patch('pdf.views.pdf_views.get_viewer_theme_and_color')
    def test_view_get(self, mock_get_viewer_theme_and_color):
        mock_get_viewer_theme_and_color.return_value = ('dark', '4 4 4')

        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')
        pdf.current_page = 4
        pdf.revision = 3
        pdf.save()
        self.assertEqual(pdf.views, 0)
        self.assertEqual(pdf.last_viewed_date, datetime(2000, 1, 1, tzinfo=timezone.utc))

        response = self.client.get(reverse('view_pdf', kwargs={'identifier': pdf.id}))

        # check that views increased by one
        pdf = self.user.profile.current_collection.pdfs.get(name='pdf')
        self.assertEqual(pdf.views, 1)
        time_diff = datetime.now(timezone.utc) - pdf.last_viewed_date
        self.assertLess(time_diff.total_seconds(), 1)

        self.assertEqual(response.context['pdf_id'], str(pdf.id))
        self.assertEqual(response.context['tab_title'], str(pdf.name))
        self.assertEqual(response.context['current_page'], 4)
        self.assertEqual(response.context['revision'], 3)
        self.assertEqual(response.context['theme'], 'dark')
        self.assertEqual(response.context['theme_color'], '4 4 4')
        self.assertEqual(response.context['user_view_bool'], True)
        self.assertEqual(response.context['keep_screen_awake'], 'Disabled')

    def test_view_get_different_page(self):
        # in this test we are just interested if the current_page is set to the value specified by the query.
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        self.assertEqual(pdf.current_page, 1)

        response = self.client.get(f"{reverse('view_pdf', kwargs={'identifier': pdf.id})}?page=20")

        self.assertEqual(response.context['current_page'], '20')

    def test_get_notes_no_htmx(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')
        response = self.client.get(reverse('get_notes', kwargs={'identifier': pdf.id}))

        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)

    def test_get_notes_htmx(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf', notes='PdfDing')
        headers = {'HTTP_HX-Request': 'true'}

        response = self.client.get(reverse('get_notes', kwargs={'identifier': pdf.id}), **headers)

        self.assertEqual(response.context['pdf_notes'], '<p>PdfDing</p>')
        self.assertTemplateUsed(response, 'partials/notes.html')

    def test_show_preview_no_htmx(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')
        response = self.client.get(reverse('show_preview', kwargs={'identifier': pdf.id}))

        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)

    def test_show_preview_htmx(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf', notes='PdfDing')
        headers = {'HTTP_HX-Request': 'true'}

        response = self.client.get(reverse('show_preview', kwargs={'identifier': pdf.id}), **headers)

        self.assertEqual(response.context['pdf_id'], pdf.id)
        self.assertEqual(response.context['preview_available'], False)
        self.assertTemplateUsed(response, 'partials/preview.html')

        dummy_path = Path(__file__).parents[1] / 'data' / 'dummy.pdf'

        with dummy_path.open(mode="rb") as f:
            file = File(f, name='dummy')
            pdf.preview = file
            pdf.save()

        response = self.client.get(reverse('show_preview', kwargs={'identifier': pdf.id}), **headers)

        self.assertEqual(response.context['pdf_id'], pdf.id)
        self.assertEqual(response.context['preview_available'], True)
        self.assertTemplateUsed(response, 'partials/preview.html')

    def test_update_page_post(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        response = self.client.post(reverse('update_page'), data={'pdf_id': pdf.id, 'current_page': 10})

        # get pdf again with the changes
        pdf = self.user.profile.current_pdfs.get(id=pdf.id)

        self.assertEqual(pdf.current_page, 10)
        self.assertEqual(200, response.status_code)

    def test_update_pdf_post_wrong_file_type(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        file_path = Path(__file__)
        with file_path.open(mode="rb") as f:
            file = File(f, name='dummy')
            response = self.client.post(reverse('update_pdf'), data={'pdf_id': pdf.id, 'updated_pdf': file})

        self.assertEqual(response.status_code, 422)

    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.set_highlights_and_comments')
    def test_update_pdf_post_correct(self, mock_set_highlights_and_comments):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        # assign empty file and check size
        init_file_path = Path(__file__).parents[1] / '__init__.py'
        with init_file_path.open(mode="rb") as f:
            file = File(f, name='dummy')
            pdf.file = file
            pdf.save()

        self.assertEqual(pdf.file.size, 0)
        self.assertEqual(pdf.revision, 0)

        # change the file and check size
        dummy_path = Path(__file__).parents[1] / 'data' / 'dummy.pdf'
        with dummy_path.open(mode="rb") as f:
            file = File(f, name='dummy')
            response = self.client.post(reverse('update_pdf'), data={'pdf_id': pdf.id, 'updated_pdf': file})

        pdf = Pdf.objects.get(id=pdf.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(pdf.file.size, 8885)
        self.assertEqual(pdf.revision, 1)
        mock_set_highlights_and_comments.assert_called_once_with(pdf)

    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.set_highlights_and_comments')
    @override_settings(DEMO_MODE=True)
    def test_update_pdf_post_demo_mode(self, mock_set_highlights_and_comments):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        # assign empty file and check size
        init_file_path = Path(__file__).parents[1] / '__init__.py'
        with init_file_path.open(mode="rb") as f:
            file = File(f, name='dummy')
            pdf.file = file
            pdf.save()

        self.assertEqual(pdf.file.size, 0)

        response = self.client.post(reverse('update_pdf'), data={'pdf_id': pdf.id})

        pdf = Pdf.objects.get(id=pdf.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(pdf.file.size, DEMO_FILE_SIZE)
        mock_set_highlights_and_comments.assert_called_once_with(pdf)

    def test_star(self):
        headers = {'HTTP_HX-Request': 'true'}
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf', starred=False)

        # star the pdf
        response = self.client.post(reverse('star', kwargs={'identifier': pdf.id}), **headers)
        pdf = Pdf.objects.get(id=pdf.id)
        self.assertTrue(pdf.starred)
        self.assertEqual(response.status_code, 200)

        # unstar the pdf
        response = self.client.post(reverse('star', kwargs={'identifier': pdf.id}), **headers)
        pdf = Pdf.objects.get(id=pdf.id)
        self.assertFalse(pdf.starred)
        self.assertEqual(response.status_code, 200)

    def test_star_unarchive(self):
        headers = {'HTTP_HX-Request': 'true'}
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf', archived=True)

        # star the pdf
        response = self.client.post(reverse('star', kwargs={'identifier': pdf.id}), **headers)
        pdf = Pdf.objects.get(id=pdf.id)
        self.assertTrue(pdf.starred)
        self.assertFalse(pdf.archived)
        self.assertEqual(response.status_code, 200)

    def test_star_no_htmx(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        response = self.client.post(reverse('star', kwargs={'identifier': pdf.id}))
        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)

    def test_archive(self):
        headers = {'HTTP_HX-Request': 'true'}
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf', archived=False)

        # archive the pdf
        response = self.client.post(reverse('archive', kwargs={'identifier': pdf.id}), **headers)
        pdf = Pdf.objects.get(id=pdf.id)
        self.assertTrue(pdf.archived)
        self.assertEqual(response.status_code, 200)

        # unarchive the pdf
        response = self.client.post(reverse('archive', kwargs={'identifier': pdf.id}), **headers)
        pdf = Pdf.objects.get(id=pdf.id)
        self.assertFalse(pdf.archived)
        self.assertEqual(response.status_code, 200)

    def test_archive_unstar(self):
        headers = {'HTTP_HX-Request': 'true'}
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf', starred=True)

        # archive the pdf
        response = self.client.post(reverse('archive', kwargs={'identifier': pdf.id}), **headers)
        pdf = Pdf.objects.get(id=pdf.id)
        self.assertTrue(pdf.archived)
        self.assertFalse(pdf.starred)
        self.assertEqual(response.status_code, 200)

    def test_archive_no_htmx(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        response = self.client.post(reverse('archive', kwargs={'identifier': pdf.id}))
        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)

    def test_delete_get_no_htmx(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        response = self.client.get(reverse('delete_pdf', kwargs={'identifier': pdf.id}))
        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)

    def test_delete_get(self):
        headers = {'HTTP_HX-Request': 'true'}
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf', starred=True)

        # archive the pdf
        response = self.client.get(reverse('delete_pdf', kwargs={'identifier': pdf.id}), **headers)

        self.assertEqual(response.context['pdf_name'], 'pdf')
        self.assertEqual(response.context['pdf_id'], str(pdf.id))
        self.assertTemplateUsed(response, 'partials/delete_pdf.html')

    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.export_annotations')
    def test_export_annotations_with_identifier(self, mock_export_annotations):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        export_path = PdfProcessingServices.get_annotation_export_path(str(self.user.id))
        export_path.parent.mkdir(exist_ok=True)
        export_path.touch()
        self.client.get(reverse('export_annotations', kwargs={'kind': 'comments', 'identifier': pdf.id}))

        # assert that the file was deleted
        self.assertFalse(export_path.exists())
        mock_export_annotations.assert_called_once_with(self.user.profile, 'comments', pdf)

        export_path.parent.rmdir()

    @mock.patch('pdf.views.pdf_views.PdfProcessingServices.export_annotations')
    def test_export_annotations_without_identifier(self, mock_export_annotations):
        Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        export_path = PdfProcessingServices.get_annotation_export_path(str(self.user.id))
        export_path.parent.mkdir(exist_ok=True)
        export_path.touch()
        self.client.get(reverse('export_annotations', kwargs={'kind': 'highlights'}))

        # assert that the file was deleted
        self.assertFalse(export_path.exists())
        mock_export_annotations.assert_called_once_with(self.user.profile, 'highlights')

        export_path.parent.rmdir()


class TestAnnotationMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    def test_filter_highlights(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        highlight_1 = PdfHighlight.objects.create(text='highlight_1', page=1, creation_date=pdf.creation_date, pdf=pdf)
        highlight_2 = PdfHighlight.objects.create(text='highlight_2', page=2, creation_date=pdf.creation_date, pdf=pdf)

        other_ws = create_workspace('other_ws', creator=self.user)
        other_ws_pdf = Pdf.objects.create(collection=other_ws.collections[0], name='other_ws_pdf')
        PdfHighlight.objects.create(text='highlight_2', page=2, creation_date=pdf.creation_date, pdf=other_ws_pdf)

        # dummy request
        response = self.client.get(reverse('pdf_overview'))

        filtered_highlights = pdf_views.HighlightOverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(sorted(list(filtered_highlights), key=lambda a: a.text), [highlight_1, highlight_2])

    def test_filter_comments(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        comment_1 = PdfComment.objects.create(text='comment_1', page=1, creation_date=pdf.creation_date, pdf=pdf)
        comment_2 = PdfComment.objects.create(text='comment_2', page=2, creation_date=pdf.creation_date, pdf=pdf)

        other_ws = create_workspace('other_ws', creator=self.user)
        other_ws_pdf = Pdf.objects.create(collection=other_ws.collections[0], name='other_ws_pdf')
        PdfComment.objects.create(text='highlight_2', page=2, creation_date=pdf.creation_date, pdf=other_ws_pdf)

        # dummy request
        response = self.client.get(reverse('pdf_overview'))

        filtered_comments = pdf_views.CommentOverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(sorted(list(filtered_comments), key=lambda a: a.text), [comment_1, comment_2])

    def test_filter_details_highlights(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')
        highlight_1 = PdfHighlight.objects.create(text='highlight_1', page=1, creation_date=pdf.creation_date, pdf=pdf)
        highlight_2 = PdfHighlight.objects.create(text='highlight_2', page=2, creation_date=pdf.creation_date, pdf=pdf)

        # we create a second pdf to verify only the highlights of correct pdf will be returned
        other_pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='other_pdf')
        PdfHighlight.objects.create(text='other_highlight', page=1, creation_date=pdf.creation_date, pdf=other_pdf)

        # dummy request
        response = self.client.get(reverse('pdf_overview'))

        filtered_highlights = pdf_views.DetailsHighlightOverviewMixin.filter_objects(response.wsgi_request, pdf.id)

        self.assertEqual(sorted(list(filtered_highlights), key=lambda a: a.text), [highlight_1, highlight_2])

    def test_filter_details_comments(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        comment_1 = PdfComment.objects.create(text='comment_1', page=1, creation_date=pdf.creation_date, pdf=pdf)
        comment_2 = PdfComment.objects.create(text='comment_2', page=2, creation_date=pdf.creation_date, pdf=pdf)

        # we create a second pdf to verify only the highlights of correct pdf will be returned
        other_pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='other_pdf')
        PdfComment.objects.create(text='other_comment', page=1, creation_date=pdf.creation_date, pdf=other_pdf)

        # dummy request
        response = self.client.get(reverse('pdf_overview'))

        filtered_comments = pdf_views.DetailsCommentOverviewMixin.filter_objects(response.wsgi_request, pdf.id)

        self.assertEqual(sorted(list(filtered_comments), key=lambda a: a.text), [comment_1, comment_2])

    def test_details_highlights_get_extra_context(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        # dummy request
        response = self.client.get(reverse('pdf_overview'))

        generated_extra_context = pdf_views.DetailsHighlightOverviewMixin.get_extra_context(
            response.wsgi_request, pdf.id
        )
        expected_extra_context = {
            'page': 'pdf_details_highlights',
            'get_next_overview_page': 'get_next_pdf_details_highlight_overview_page',
            'pdf': pdf,
            'kind': 'highlights',
        }

        self.assertEqual(generated_extra_context, expected_extra_context)

    def test_details_comments_get_extra_context(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')

        # dummy request
        response = self.client.get(reverse('pdf_overview'))

        generated_extra_context = pdf_views.DetailsCommentOverviewMixin.get_extra_context(response.wsgi_request, pdf.id)
        expected_extra_context = {
            'page': 'pdf_details_comments',
            'get_next_overview_page': 'get_next_pdf_details_comment_overview_page',
            'pdf': pdf,
            'kind': 'comments',
        }

        self.assertEqual(generated_extra_context, expected_extra_context)
