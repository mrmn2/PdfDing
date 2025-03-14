from datetime import datetime, timezone
from pathlib import Path
from unittest import mock
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from pdf import forms
from pdf.models import Pdf, PdfComment, PdfHighlight, Tag
from pdf.views import pdf_views

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

    def test_get_context_get(self):
        add_pdf_mixin = pdf_views.AddPdfMixin()
        generated_context = add_pdf_mixin.get_context_get(None, None)

        self.assertEqual({'form': forms.AddForm}, generated_context)

    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.process_with_pypdfium')
    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_obj_save(self, mock_from_buffer, mock_process_with_pypdfium, mock_set_highlights_and_comments):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'test1.pdf'
        form = forms.AddForm(
            data={
                'name': 'some_pdf',
                'tag_string': 'tag_a tag_2',
                'description': 'some_description',
                'notes': 'some_notes',
            },
            owner=self.user.profile,
            files={'file': file_mock},
        )

        pdf_views.AddPdfMixin.obj_save(form, response.wsgi_request, None)

        pdf = self.user.profile.pdf_set.get(name='some_pdf')
        tag_names = [tag.name for tag in pdf.tags.all()]
        self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})
        self.assertEqual(pdf.notes, 'some_notes')
        self.assertEqual(pdf.description, 'some_description')
        self.assertEqual(pdf.owner, self.user.profile)
        self.assertEqual(pdf.file.size, 0)  # mock file has size 0
        mock_process_with_pypdfium.assert_called_once_with(pdf)
        mock_set_highlights_and_comments.assert_called_once_with(pdf)

    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.process_with_pypdfium')
    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_obj_save_use_file_name(
        self, mock_from_buffer, mock_process_with_pypdfium, mock_set_highlights_and_comments
    ):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'test1.pdf'
        form = forms.AddForm(
            data={'name': 'bla', 'tag_string': 'tag_a tag_2', 'use_file_name': True},
            owner=self.user.profile,
            files={'file': file_mock},
        )

        pdf_views.AddPdfMixin.obj_save(form, response.wsgi_request, None)

        pdf = self.user.profile.pdf_set.get(name='test1')
        tag_names = [tag.name for tag in pdf.tags.all()]
        self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})
        self.assertEqual(pdf.owner, self.user.profile)

        mock_process_with_pypdfium.assert_called_once_with(pdf)
        mock_set_highlights_and_comments.assert_called_once_with(pdf)

    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.process_with_pypdfium')
    @override_settings(DEMO_MODE=True)
    def test_obj_save_demo_mode(self, mock_process_with_pypdfium, mock_set_highlights_and_comments):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        form = forms.AddFormNoFile(data={'name': 'some_pdf', 'tag_string': 'tag_a tag_2'}, owner=self.user.profile)

        pdf_views.AddPdfMixin.obj_save(form, response.wsgi_request, None)

        pdf = self.user.profile.pdf_set.get(name='some_pdf')
        tag_names = [tag.name for tag in pdf.tags.all()]
        self.assertEqual(pdf.owner, self.user.profile)
        self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})
        self.assertEqual(pdf.file.size, DEMO_FILE_SIZE)

        mock_process_with_pypdfium.assert_called_once_with(pdf)
        mock_set_highlights_and_comments.assert_called_once_with(pdf)


class TestBulkAddPDFMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    def test_get_context_get(self):
        add_pdf_mixin = pdf_views.BulkAddPdfMixin()
        generated_context = add_pdf_mixin.get_context_get(None, None)

        self.assertEqual({'form': forms.BulkAddForm}, generated_context)

    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.process_with_pypdfium')
    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_obj_save_single_file_no_skipping(
        self, mock_from_buffer, mock_process_with_pypdfium, mock_set_highlights_and_comments
    ):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'test1.pdf'
        form = forms.BulkAddForm(
            data={'tag_string': 'tag_a tag_2', 'description': ''},
            owner=self.user.profile,
            files=MultiValueDict({'file': [file_mock]}),
        )

        pdf_views.BulkAddPdfMixin.obj_save(form, response.wsgi_request, None)

        pdf = self.user.profile.pdf_set.get(name='test1')
        tag_names = [tag.name for tag in pdf.tags.all()]
        self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})
        self.assertEqual(pdf.owner, self.user.profile)
        self.assertEqual(pdf.file.size, 0)  # mock file has size 0
        mock_process_with_pypdfium.assert_called_once_with(pdf)
        mock_set_highlights_and_comments.assert_called_once_with(pdf)

    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.process_with_pypdfium')
    @mock.patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_obj_save_multiple_files_no_skipping(
        self, mock_from_buffer, mock_process_with_pypdfium, mock_set_highlights_and_comments
    ):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        file_mock_1 = mock.MagicMock(spec=File, name='FileMock1')
        file_mock_1.name = 'test1.pdf'
        file_mock_2 = mock.MagicMock(spec=File, name='FileMock2')
        file_mock_2.name = 'test2.pdf'
        form = forms.BulkAddForm(
            data={'tag_string': 'tag_a tag_2', 'description': 'some_description', 'notes': 'some_notes'},
            owner=self.user.profile,
            files=MultiValueDict({'file': [file_mock_1, file_mock_2]}),
        )

        pdf_views.BulkAddPdfMixin.obj_save(form, response.wsgi_request, None)

        for name in ['test1', 'test2']:
            pdf = self.user.profile.pdf_set.get(name=name)
            tag_names = [tag.name for tag in pdf.tags.all()]
            self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})
            self.assertEqual(pdf.description, 'some_description')
            self.assertEqual(pdf.notes, 'some_notes')
            self.assertEqual(pdf.owner, self.user.profile)
            # check that pdf pages are set to -1 in case of exception.
            # in this test there should be an exception as a mock file is used.
            self.assertEqual(pdf.number_of_pages, -1)

    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.process_with_pypdfium')
    @mock.patch('pdf.service.uuid4', return_value='123456789')
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
            old_pdf = Pdf.objects.create(owner=self.user.profile, name=f'test{i}', file=simple_file)
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
            data={'tag_string': 'tag_a tag_2', 'description': 'description', 'skip_existing': 'on'},
            owner=self.user.profile,
            files=MultiValueDict({'file': files}),
        )

        pdf_views.BulkAddPdfMixin.obj_save(form, response.wsgi_request, None)

        expected_pdf_names = ['test1', 'test2', 'test2_12345678', 'test3']
        generated_pdf_names = [pdf.name for pdf in self.user.profile.pdf_set.all()]
        self.assertEqual(expected_pdf_names, generated_pdf_names)

        # also check date the test1 and test2 are unchanged
        for i in range(2):
            self.assertEqual(old_pdfs[i], self.user.profile.pdf_set.get(name=f'test{i + 1}'))

    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.set_highlights_and_comments')
    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.process_with_pypdfium')
    @override_settings(DEMO_MODE=True)
    def test_obj_save_demo_mode(self, mock_process_with_pypdfium, mock_set_highlights_and_comments):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        form = forms.BulkAddFormNoFile(
            data={'tag_string': 'tag_a tag_2', 'description': 'description'}, owner=self.user.profile
        )

        pdf_views.BulkAddPdfMixin.obj_save(form, response.wsgi_request, None)

        pdf = self.user.profile.pdf_set.get(name='demo')
        tag_names = [tag.name for tag in pdf.tags.all()]
        self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})
        self.assertEqual('description', 'description')
        self.assertEqual(pdf.owner, self.user.profile)
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
            pdf = Pdf.objects.create(owner=self.user.profile, name=f'pdf_{i % 5}_{i}')

            # add a tag to pdf 2, 7
            if i % 5 == 2 and i < 10:
                tag = Tag.objects.create(name=f'tag_{i}', owner=self.user.profile)
                pdf.tags.set([tag])

        pdf_1 = Pdf.objects.create(owner=self.user.profile, name='pdf_to_be_found_1')
        pdf_2 = Pdf.objects.create(owner=self.user.profile, name='pdf_to_be_found_2')
        pdf_3 = Pdf.objects.create(owner=self.user.profile, name='not_to_be_found')
        tags = []

        for name in ['programming', 'programming/python', 'programming/python/django', 'programming/python/flask']:
            tag = Tag.objects.create(name=name, owner=self.user.profile)
            tags.append(tag)

        pdf_1.tags.set(tags)
        pdf_2.tags.set(tags[2:3])
        pdf_3.tags.set(tags)

        response = self.client.get(f'{reverse('pdf_overview')}?search=pdf_&tags=programming/python')

        filtered_pdfs = pdf_views.OverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(sorted(list(filtered_pdfs), key=lambda a: a.name), [pdf_1, pdf_2])

    def test_filter_objects_starred(self):
        pdf_1 = Pdf.objects.create(owner=self.user.profile, name='pdf_to_be_found_1', starred=True)
        pdf_2 = Pdf.objects.create(owner=self.user.profile, name='pdf_to_be_found_2', starred=True)
        Pdf.objects.create(owner=self.user.profile, name='not_to_be_found')

        response = self.client.get(f'{reverse('pdf_overview')}?selection=starred')

        filtered_pdfs = pdf_views.OverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(sorted(list(filtered_pdfs), key=lambda a: a.name), [pdf_1, pdf_2])

    def test_filter_objects_ignore_archived(self):
        pdf_1 = Pdf.objects.create(owner=self.user.profile, name='pdf_to_be_found_1')
        pdf_2 = Pdf.objects.create(owner=self.user.profile, name='pdf_to_be_found_2')
        Pdf.objects.create(owner=self.user.profile, name='not_to_be_found', archived=True)

        response = self.client.get(f'{reverse('pdf_overview')}')

        filtered_pdfs = pdf_views.OverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(sorted(list(filtered_pdfs), key=lambda a: a.name), [pdf_1, pdf_2])

    def test_filter_objects_archived(self):
        pdf_1 = Pdf.objects.create(owner=self.user.profile, name='pdf_to_be_found_1', archived=True)
        Pdf.objects.create(owner=self.user.profile, name='pdf_to_be_found_2')
        Pdf.objects.create(owner=self.user.profile, name='not_to_be_found')

        response = self.client.get(f'{reverse('pdf_overview')}?selection=archived')

        filtered_pdfs = pdf_views.OverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(list(filtered_pdfs), [pdf_1])

    def test_fuzzy_filter_pdfs(self):
        Pdf.objects.create(owner=self.user.profile, name='pdf_not_to_be_found')
        pdf_self_hosted = Pdf.objects.create(owner=self.user.profile, name='The best self-hosted applications ')
        pdf_self_hosting = Pdf.objects.create(owner=self.user.profile, name='Self-hosting Guide')
        Pdf.objects.create(owner=self.user.profile, name='self sufficiency')

        filtered_pdfs = pdf_views.OverviewMixin.fuzzy_filter_pdfs(Pdf.objects.all(), 'self hosted')
        self.assertEqual(sorted(list(filtered_pdfs), key=lambda a: a.name), [pdf_self_hosting, pdf_self_hosted])

    @patch('pdf.service.TagServices.get_tag_info_dict', return_value='tag_info_dict')
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
        }

        self.assertEqual(generated_extra_context, expected_extra_context)

    @patch('pdf.service.TagServices.get_tag_info_dict', return_value='tag_info_dict')
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
        }

        self.assertEqual(generated_extra_context, expected_extra_context)

    @patch('pdf.service.TagServices.get_tag_info_dict', return_value='tag_info_dict')
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
        }

        self.assertEqual(generated_extra_context, expected_extra_context)

    @patch('pdf.service.TagServices.get_tag_info_dict', return_value='tag_info_dict')
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
        }

        self.assertEqual(generated_extra_context, expected_extra_context)


class TestPdfMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    def test_get_object(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

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
            owner=self.user.profile, name='pdf_name', description='some_description', notes='some_note'
        )
        tags = [Tag.objects.create(name=f'tag_{i}', owner=self.user.profile) for i in range(2)]
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

    def test_process_field(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', description='something')
        tag_1 = Tag.objects.create(name='tag_1', owner=self.user.profile)
        tag_2 = Tag.objects.create(name='tag_2', owner=self.user.profile)

        pdf.tags.set([tag_1, tag_2])

        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        pdf_views.EditPdfMixin.process_field('tags', pdf, response.wsgi_request, {'tag_string': 'tag_1 tag_3'})

        # get pdf again with the changes
        pdf = self.user.profile.pdf_set.get(id=pdf.id)
        tag_names = [tag.name for tag in pdf.tags.all()]

        self.assertEqual(sorted(tag_names), sorted(['tag_1', 'tag_3']))
        # check that tag 2 was deleted
        self.assertFalse(self.user.profile.tag_set.filter(name='tag_2').exists())


class TestViews(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    @patch('pdf.views.pdf_views.get_viewer_colors')
    def test_view_get(self, mock_get_viewer_colors):
        mock_colors_dict = {
            'primary_color': '1 1 1',
            'secondary_color': '2 2 2',
            'text_color': '3 3 3',
            'theme_color': '4 4 4',
        }
        mock_get_viewer_colors.return_value = mock_colors_dict

        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')
        pdf.current_page = 4
        pdf.revision = 3
        pdf.save()
        self.assertEqual(pdf.views, 0)
        self.assertEqual(pdf.last_viewed_date, datetime(2000, 1, 1, tzinfo=timezone.utc))

        response = self.client.get(reverse('view_pdf', kwargs={'identifier': pdf.id}))

        # check that views increased by one
        pdf = self.user.profile.pdf_set.get(name='pdf')
        self.assertEqual(pdf.views, 1)
        time_diff = datetime.now(timezone.utc) - pdf.last_viewed_date
        self.assertLess(time_diff.total_seconds(), 1)

        self.assertEqual(response.context['pdf_id'], str(pdf.id))
        self.assertEqual(response.context['tab_title'], str(pdf.name))
        self.assertEqual(response.context['current_page'], 4)
        self.assertEqual(response.context['revision'], 3)
        self.assertEqual(response.context['primary_color'], mock_colors_dict['primary_color'])
        self.assertEqual(response.context['secondary_color'], mock_colors_dict['secondary_color'])
        self.assertEqual(response.context['text_color'], mock_colors_dict['text_color'])
        self.assertEqual(response.context['theme_color'], mock_colors_dict['theme_color'])
        self.assertEqual(response.context['user_view_bool'], True)

    def test_get_notes_no_htmx(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')
        response = self.client.get(reverse('get_notes', kwargs={'identifier': pdf.id}))

        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)

    def test_get_notes_htmx(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', notes='PdfDing')
        headers = {'HTTP_HX-Request': 'true'}

        response = self.client.get(reverse('get_notes', kwargs={'identifier': pdf.id}), **headers)

        self.assertEqual(response.context['pdf_notes'], '<p>PdfDing</p>')
        self.assertTemplateUsed(response, 'partials/notes.html')

    def test_show_preview_no_htmx(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')
        response = self.client.get(reverse('show_preview', kwargs={'identifier': pdf.id}))

        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)

    def test_show_preview_htmx(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', notes='PdfDing')
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
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        response = self.client.post(reverse('update_page'), data={'pdf_id': pdf.id, 'current_page': 10})

        # get pdf again with the changes
        pdf = self.user.profile.pdf_set.get(id=pdf.id)

        self.assertEqual(pdf.current_page, 10)
        self.assertEqual(200, response.status_code)

    def test_update_pdf_post_wrong_file_type(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        file_path = Path(__file__)
        with file_path.open(mode="rb") as f:
            file = File(f, name='dummy')
            response = self.client.post(reverse('update_pdf'), data={'pdf_id': pdf.id, 'updated_pdf': file})

        self.assertEqual(response.status_code, 422)

    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.set_highlights_and_comments')
    def test_update_pdf_post_correct(self, mock_set_highlights_and_comments):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

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

    @mock.patch('pdf.views.pdf_views.service.PdfProcessingServices.set_highlights_and_comments')
    @override_settings(DEMO_MODE=True)
    def test_update_pdf_post_demo_mode(self, mock_set_highlights_and_comments):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

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
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', starred=False)

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
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', archived=True)

        # star the pdf
        response = self.client.post(reverse('star', kwargs={'identifier': pdf.id}), **headers)
        pdf = Pdf.objects.get(id=pdf.id)
        self.assertTrue(pdf.starred)
        self.assertFalse(pdf.archived)
        self.assertEqual(response.status_code, 200)

    def test_star_no_htmx(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        response = self.client.post(reverse('star', kwargs={'identifier': pdf.id}))
        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)

    def test_archive(self):
        headers = {'HTTP_HX-Request': 'true'}
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', archived=False)

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
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', starred=True)

        # archive the pdf
        response = self.client.post(reverse('archive', kwargs={'identifier': pdf.id}), **headers)
        pdf = Pdf.objects.get(id=pdf.id)
        self.assertTrue(pdf.archived)
        self.assertFalse(pdf.starred)
        self.assertEqual(response.status_code, 200)

    def test_archive_no_htmx(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        response = self.client.post(reverse('archive', kwargs={'identifier': pdf.id}))
        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)

    def test_delete_get_no_htmx(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        response = self.client.get(reverse('delete_pdf', kwargs={'identifier': pdf.id}))
        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)

    def test_delete_get(self):
        headers = {'HTTP_HX-Request': 'true'}
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', starred=True)

        # archive the pdf
        response = self.client.get(reverse('delete_pdf', kwargs={'identifier': pdf.id}), **headers)

        self.assertEqual(response.context['pdf_name'], 'pdf')
        self.assertEqual(response.context['pdf_id'], str(pdf.id))
        self.assertTemplateUsed(response, 'partials/delete_pdf.html')


class TestAnnotationMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    def test_filter_highlights(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        highlight_1 = PdfHighlight.objects.create(text='highlight_1', page=1, creation_date=pdf.creation_date, pdf=pdf)
        highlight_2 = PdfHighlight.objects.create(text='highlight_2', page=2, creation_date=pdf.creation_date, pdf=pdf)

        # dummy request
        response = self.client.get(reverse('pdf_overview'))

        filtered_highlights = pdf_views.HighlightOverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(sorted(list(filtered_highlights), key=lambda a: a.text), [highlight_1, highlight_2])

    def test_filter_comments(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        comment_1 = PdfComment.objects.create(text='comment_1', page=1, creation_date=pdf.creation_date, pdf=pdf)
        comment_2 = PdfComment.objects.create(text='comment_2', page=2, creation_date=pdf.creation_date, pdf=pdf)

        # dummy request
        response = self.client.get(reverse('pdf_overview'))

        filtered_comments = pdf_views.CommentOverviewMixin.filter_objects(response.wsgi_request)

        self.assertEqual(sorted(list(filtered_comments), key=lambda a: a.text), [comment_1, comment_2])
