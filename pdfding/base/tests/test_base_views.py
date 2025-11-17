from pathlib import Path
from unittest.mock import patch

from base.tests import base_view_definitions
from core.settings import MEDIA_ROOT
from core.urls import urlpatterns as base_patterns
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http.response import HttpResponse
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import path, reverse
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh
from pdf.forms import AddForm, DescriptionForm
from pdf.models.pdf_models import Pdf
from users.models import Profile

test_patterns = [
    path('test/add/<identifier>', base_view_definitions.Add.as_view(), name='test_add'),
    path('test/overview/<items_per_page>', base_view_definitions.Overview.as_view(), name='test_overview'),
    path('test/overview/<page>/<items_per_page>', base_view_definitions.Overview.as_view(), name='test_get_next_page'),
    path('test/overview_query', base_view_definitions.OverviewQuery.as_view(), name='test_overview_query'),
    path('test/serve/<identifier>', base_view_definitions.Serve.as_view(), name='test_serve'),
    path('test/download/<identifier>', base_view_definitions.Download.as_view(), name='test_download'),
    path('test/details/<identifier>', base_view_definitions.Details.as_view(), name='test_details'),
    path('test/delete/<identifier>', base_view_definitions.Delete.as_view(), name='test_delete'),
    path('test/edit/<identifier>/<field_name>', base_view_definitions.Edit.as_view(), name='test_edit'),
]

urlpatterns = base_patterns + test_patterns


def set_up(self):
    self.client = Client()
    self.user = User.objects.create_user(username=self.username, password=self.password, email='a@a.com')
    self.client.login(username=self.username, password=self.password)


class TestViews(TestCase):

    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    @override_settings(ROOT_URLCONF=__name__)
    def test_base_add_get(self):
        response = self.client.get(reverse('test_add', kwargs={'identifier': 'some_id'}))

        self.assertEqual(response.context['form'], AddForm)
        self.assertEqual(response.context['other'], 1234)
        self.assertTemplateUsed(response, 'add_pdf.html')

    @override_settings(ROOT_URLCONF=__name__)
    def test_add_post_invalid_form(self):
        response = self.client.post(reverse('test_add', kwargs={'identifier': 'some_id'}), data={'name': 'pdf'})

        self.assertIsInstance(response.context['form'], AddForm)
        self.assertTemplateUsed(response, 'add_pdf.html')

    @override_settings(ROOT_URLCONF=__name__)
    @patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_base_add_post(self, mock_from_buffer):
        simple_file = SimpleUploadedFile("simple.pdf", b"these are the file contents!")

        response = self.client.post(
            reverse('test_add', kwargs={'identifier': 'some_id'}),
            data={'name': 'pdf', 'description': 'something', 'tag_string': 'tag_a tag_2', 'file': simple_file},
        )

        pdfs = self.user.profile.pdfs

        for pdf in pdfs:
            Path(pdf.file.path).unlink()
            self.assertEqual(pdf.name, 'pdf_some_id')

        self.assertEqual(len(pdfs), 1)
        self.assertRedirects(response, reverse('pdf_overview'))

    @patch('base.base_views.BaseOverview.do_extra_action')
    @override_settings(ROOT_URLCONF=__name__)
    def test_overview_get(self, mock_do_extra_action):
        # Also test sorting by title with capitalization taken into account
        self.user.profile.pdf_sorting = Profile.PdfSortingChoice.NAME_DESC
        self.user.profile.save()

        # create some pdfs
        # Kaki and fig need be removed by the filter function
        for pdf_name in ['orange', 'banana', 'Apple', 'Raspberry', 'Kaki', 'fig']:
            Pdf.objects.create(owner=self.user.profile, name=pdf_name)

        response = self.client.get(f'{reverse('test_overview', kwargs={'items_per_page': 3})}')
        pdf_names = [pdf.name for pdf in response.context['page_obj']]

        self.assertEqual(pdf_names, ['Raspberry', 'orange', 'banana'])
        self.assertEqual(response.context['other'], 1234)
        self.assertEqual(response.context['next_page_available'], True)
        self.assertEqual(response.context['items_per_page'], '3')
        self.assertEqual(str(response.context['sorting']), 'OrderBy(Lower(F(name)), descending=True)')
        self.assertTemplateUsed(response, 'pdf_overview.html')
        mock_do_extra_action.assert_called_once_with(response.wsgi_request)

    @patch('base.base_views.BaseOverview.do_extra_action')
    @override_settings(ROOT_URLCONF=__name__)
    def test_overview_get_htmx(self, mock_do_extra_action):
        # Also test sorting by title with capitalization taken into account
        self.user.profile.pdf_sorting = Profile.PdfSortingChoice.NAME_DESC
        self.user.profile.save()
        headers = {'HTTP_HX-Request': 'true'}

        # create some pdfs
        # Kaki and fig need be removed by the filter function
        for pdf_name in ['orange', 'banana', 'Apple', 'Raspberry', 'Kaki', 'fig']:
            Pdf.objects.create(owner=self.user.profile, name=pdf_name)

        response = self.client.get(
            f'{reverse('test_get_next_page', kwargs={'items_per_page': 3, 'page': 2})}', **headers
        )
        pdf_names = [pdf.name for pdf in response.context['page_obj']]

        # since we are getting the second page only apple should be there and no next page
        self.assertEqual(pdf_names, ['Apple'])
        self.assertEqual(response.context['other'], 1234)
        self.assertEqual(response.context['next_page_available'], False)
        self.assertEqual(response.context['items_per_page'], '3')
        self.assertEqual(response.context['current_page'], '2')
        self.assertEqual(str(response.context['sorting']), 'OrderBy(Lower(F(name)), descending=True)')
        self.assertTemplateUsed(response, 'includes/pdf_overview/overview_page.html')
        mock_do_extra_action.assert_not_called()

    @override_settings(ROOT_URLCONF=__name__)
    @patch('base.base_views.construct_query_overview_url')
    def test_overview_query_get(self, mock_construct_query_overview_url):
        mock_return_value = f'{reverse('pdf_overview')}?search=searching'
        mock_construct_query_overview_url.return_value = mock_return_value
        response = self.client.get(
            f'{reverse('test_overview_query')}' '?search=searching&tags=tag&selection=starred&remove=other_tag'
        )

        mock_construct_query_overview_url.assert_called_once_with(
            'pdf_overview', 'searching', 'starred', 'other_tag', 'pdf'
        )
        self.assertRedirects(response, mock_return_value, status_code=302)

    @override_settings(ROOT_URLCONF=__name__)
    @patch('base.base_views.construct_query_overview_url')
    def test_overview_query_get_no_queries(self, mock_construct_query_overview_url):
        mock_return_value = f'{reverse('pdf_overview')}?search=searching'
        mock_construct_query_overview_url.return_value = mock_return_value
        response = self.client.get(reverse('test_overview_query'))

        mock_construct_query_overview_url.assert_called_once_with('pdf_overview', '', '', '', 'pdf')
        self.assertRedirects(response, mock_return_value, status_code=302)

    @override_settings(ROOT_URLCONF=__name__)
    @patch('base.base_views.serve')
    def test_serve_get(self, mock_serve):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')
        pdf.file.name = f'{self.user}/pdf_name'
        pdf.save()
        mock_serve.return_value = HttpResponse('some response')

        response = self.client.get(reverse('test_serve', kwargs={'identifier': pdf.id}))

        mock_serve.assert_called_with(response.wsgi_request, document_root=MEDIA_ROOT, path=f'{self.user}/pdf_name')

    @override_settings(ROOT_URLCONF=__name__)
    def test_download_get(self):
        simple_file = SimpleUploadedFile("simple.pdf", b"these are the file contents!")
        pdf = Pdf.objects.create(owner=self.user.profile, name='name', file=simple_file)
        pdf_path = Path(pdf.file.path)

        response = self.client.get(reverse('test_download', kwargs={'identifier': pdf.id}))

        pdf_path.unlink()

        self.assertEqual(response.filename, f'{pdf.name}.pdf')
        self.assertTrue(response.as_attachment)

    @override_settings(ROOT_URLCONF=__name__)
    def test_details_get(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        # test without http referer
        response = self.client.get(reverse('test_details', kwargs={'identifier': pdf.id}))

        self.assertEqual(response.context['pdf'], pdf)
        self.assertTemplateUsed(response, 'pdf_details.html')

        # test without sort query
        response = self.client.get(
            reverse('test_details', kwargs={'identifier': pdf.id}), HTTP_REFERER='pdfding.com/details/?q=search'
        )

        self.assertEqual(response.context['pdf'], pdf)

    @override_settings(ROOT_URLCONF=__name__)
    def test_edit_get_no_htmx(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        response = self.client.get(reverse('test_edit', kwargs={'identifier': pdf.id, 'field_name': 'description'}))
        self.assertRedirects(response, reverse('pdf_details', kwargs={'identifier': pdf.id}), status_code=302)

    @override_settings(ROOT_URLCONF=__name__)
    def test_edit_get_htmx(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')
        headers = {'HTTP_HX-Request': 'true'}

        response = self.client.get(
            reverse('test_edit', kwargs={'identifier': pdf.id, 'field_name': 'description'}), **headers
        )

        self.assertEqual(response.context['edit_id'], 'description-edit')
        self.assertEqual(response.context['field_name'], 'description')
        self.assertEqual(response.context['details_url'], reverse('pdf_details', kwargs={'identifier': pdf.id}))
        self.assertEqual(
            response.context['action_url'],
            reverse('edit_pdf', kwargs={'field_name': 'description', 'identifier': pdf.id}),
        )
        self.assertIsInstance(response.context['form'], DescriptionForm)
        self.assertTemplateUsed(response, 'partials/details_form.html')

    @override_settings(ROOT_URLCONF=__name__)
    def test_edit_post_invalid_form(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', description='something')

        # post is invalid because data is missing
        # follow=True is needed for getting the message
        response = self.client.post(
            reverse('test_edit', kwargs={'identifier': pdf.id, 'field_name': 'name'}),
            follow=True,
        )
        message = list(response.context['messages'])[0]

        self.assertEqual(message.message, 'This field is required.')
        self.assertEqual(message.tags, 'warning')

    @override_settings(ROOT_URLCONF=__name__)
    def test_edit_post_not_name_not_processed(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', description='something')

        self.client.post(
            reverse('test_edit', kwargs={'identifier': pdf.id, 'field_name': 'description'}),
            data={'description': 'new'},
        )

        # get pdf again with the changes
        pdf = self.user.profile.pdfs.get(id=pdf.id)

        self.assertEqual(pdf.description, 'new')

    @override_settings(ROOT_URLCONF=__name__)
    def test_edit_post_processed(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', description='something')

        self.client.post(
            reverse('test_edit', kwargs={'identifier': pdf.id, 'field_name': 'process_description'}),
            data={'process_description': 'description'},
        )

        # get pdf again with the changes
        pdf = self.user.profile.pdfs.get(id=pdf.id)

        self.assertEqual(pdf.description, 'processed_description')


# we need the TransactionTestCase class because otherwise django_cleanup will not delete the file
class TestDelete(TransactionTestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    @override_settings(ROOT_URLCONF=__name__)
    def test_delete_htmx_not_from_details(self):
        # create a file for the test, so we can check that it was deleted by django_cleanup
        simple_file = SimpleUploadedFile("simple.pdf", b"these are the file contents!")
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', file=simple_file)
        pdf_path = Path(pdf.file.path)

        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.delete(reverse('test_delete', kwargs={'identifier': pdf.id}), **headers)

        self.assertFalse(self.user.profile.pdfs.filter(id=pdf.id).exists())
        self.assertFalse(pdf_path.exists())
        self.assertEqual(type(response), HttpResponseClientRefresh)

    @override_settings(ROOT_URLCONF=__name__)
    def test_delete_htmx_from_details(self):
        # create a file for the test, so we can check that it was deleted by django_cleanup
        simple_file = SimpleUploadedFile("simple.pdf", b"these are the file contents!")
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', file=simple_file)
        pdf_path = Path(pdf.file.path)

        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.delete(
            reverse('test_delete', kwargs={'identifier': pdf.id}), HTTP_REFERER='pdfding.com/details/xx', **headers
        )

        self.assertFalse(self.user.profile.pdfs.filter(id=pdf.id).exists())
        self.assertFalse(pdf_path.exists())
        self.assertEqual(type(response), HttpResponseClientRedirect)

    @override_settings(ROOT_URLCONF=__name__)
    def test_delete_no_htmx(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        response = self.client.delete(reverse('test_delete', kwargs={'identifier': pdf.id}))
        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)
