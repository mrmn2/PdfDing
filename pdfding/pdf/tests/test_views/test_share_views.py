from datetime import datetime, timedelta, timezone
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.http.response import Http404
from django.test import Client, TestCase
from django.urls import reverse
from pdf.forms import (
    ShareCollectionForm,
    SharedDeletionDateForm,
    SharedMaxViewsForm,
    SharedNameForm,
    SharedPasswordForm,
    ShareForm,
    ViewSharedPasswordForm,
)
from pdf.models.pdf_models import Pdf
from pdf.models.shared_models import SharedCollection, SharedPdf
from pdf.services.workspace_services import create_workspace, get_shared_collections_of_workspace
from pdf.views.share_views import (
    AddSharedCollectionMixin,
    AddSharedPdfMixin,
    CollectionOverviewMixin,
    CollectionPdfPublicMixin,
    EditSharedCollectionMixin,
    EditSharedPdfMixin,
    OverviewMixin,
    PdfPublicMixin,
    SharedCollectionMixin,
    SharedCollectionPublicView,
    SharedPdfMixin,
    SharedPdfPublicView,
)

from pdfding.pdf.views import share_views


def set_up(self):
    self.client = Client()
    self.user = User.objects.create_user(username=self.username, password=self.password, email='a@a.com')
    self.pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf')


class TestAddSharedPdfMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)
        self.client.login(username=self.username, password=self.password)

    @patch('pdf.views.share_views.AddSharedPdfMixin.form')
    def test_get_context_get(self, mock_share_form):
        # we need to create a request so get_pdf can access the user profile
        response = self.client.get(reverse('pdf_overview'))

        shared_pdf_mixin = AddSharedPdfMixin()
        generated_context = shared_pdf_mixin.get_context_get(response.wsgi_request, self.pdf.id)

        self.assertEqual(generated_context['pdf_name'], self.pdf.name)
        mock_share_form.assert_called_once_with(profile=self.user.profile)
        self.assertIsInstance(generated_context['form'], MagicMock)

    @patch('pdf.views.share_views.get_future_datetime', return_value=datetime.now(timezone.utc))
    @patch('pdf.views.share_views.AddSharedPdfMixin.add_qr_code')
    def test_obj_save(self, mock_add_qr_code, mock_get_future_datetime):
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        form = ShareForm(
            data={'name': 'some_shared_pdf', 'deletion_input': '0d2h2m'},
            profile=self.user.profile,
        )

        AddSharedPdfMixin.obj_save(form, response.wsgi_request, self.pdf.id)
        shared_pdf = self.user.profile.current_shared_pdfs.get(name='some_shared_pdf')

        self.assertEqual(shared_pdf.pdf, self.pdf)
        mock_get_future_datetime.assert_any_call('0d2h2m')
        mock_add_qr_code.assert_called_with(shared_pdf, 'view_shared_pdf', response.wsgi_request)

    @patch('pdf.views.share_views.AddSharedPdfMixin.generate_qr_code', return_value=BytesIO())
    def test_add_qr_code(self, mock_generate_qr_code):
        shared_pdf = SharedPdf.objects.create(pdf=self.pdf, name='share')
        # we need to create a request so get_pdf can access the user profile
        response = self.client.get(reverse('pdf_overview'))

        AddSharedPdfMixin.add_qr_code(shared_pdf, 'view_shared_pdf', response.wsgi_request)

        mock_generate_qr_code.assert_called_with(f'http://testserver/pdf/shared/{shared_pdf.id}')

    def test_set_access_dates(self):
        shared_pdf = SharedPdf.objects.create(pdf=self.pdf, name='share')

        AddSharedPdfMixin.set_access_dates(shared_pdf, '1d0h22m')

        # get pdf again so changes are reflected
        shared_pdf = self.user.profile.current_shared_pdfs.get(name='share')

        for generated_result in [shared_pdf.deletion_date]:
            expected_result = datetime.now(timezone.utc) + timedelta(days=1, hours=0, minutes=22)

            self.assertTrue((generated_result - expected_result).total_seconds() < 0.1)


class TestAddSharedCollectionMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)
        self.client.login(username=self.username, password=self.password)

    @patch('pdf.views.share_views.AddSharedCollectionMixin.form')
    def test_get_context_get(self, mock_share_form):
        collection = self.user.profile.current_collection

        # we need to create a request so get_pdf can access the user profile
        response = self.client.get(reverse('pdf_overview'))

        shared_collection_mixin = AddSharedCollectionMixin()
        generated_context = shared_collection_mixin.get_context_get(response.wsgi_request, collection.id)

        self.assertEqual(generated_context['collection_name'], collection.name)
        mock_share_form.assert_called_once_with(profile=self.user.profile)
        self.assertIsInstance(generated_context['form'], MagicMock)

    @patch('pdf.views.share_views.get_future_datetime', return_value=datetime.now(timezone.utc))
    @patch('pdf.views.share_views.AddSharedCollectionMixin.add_qr_code')
    def test_obj_save(self, mock_add_qr_code, mock_get_future_datetime):
        collection = self.user.profile.current_collection

        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        form = ShareCollectionForm(
            data={'name': 'some_shared_collection', 'deletion_input': '0d2h2m'},
            profile=self.user.profile,
        )

        AddSharedCollectionMixin.obj_save(form, response.wsgi_request, collection.id)
        shared_collections = get_shared_collections_of_workspace(collection.workspace)
        assert shared_collections.count() == 1

        shared_collection = shared_collections.first()

        self.assertEqual(shared_collection.collection, collection)
        mock_get_future_datetime.assert_any_call('0d2h2m')
        mock_add_qr_code.assert_called_with(shared_collection, 'view_shared_collection', response.wsgi_request)


class TestOverviewMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)

        # create some pdfs
        for i in range(1, 4):
            SharedPdf.objects.create(pdf=self.pdf, name=f'shared_{i}')

        deletion_date = datetime.now(timezone.utc) - timedelta(minutes=5)
        SharedPdf.objects.create(pdf=self.pdf, name='shared_deleted', deletion_date=deletion_date)

    def test_filter_objects(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(f'{reverse('shared_pdf_overview')}?q=pdf_2+%23tag_2')

        # make sure only current shared pdfs are userd
        other_ws = create_workspace('other_ws', creator=self.user)
        other_ws_pdf = Pdf.objects.create(collection=other_ws.collections[0], name='other_ws_pdf')
        SharedPdf.objects.create(pdf=other_ws_pdf, name='other_share')

        filtered_shares = OverviewMixin.filter_objects(response.wsgi_request)
        shared_names = [shared.name for shared in filtered_shares]

        self.assertEqual(shared_names, ['shared_1', 'shared_2', 'shared_3'])

    def test_get_extra_context(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('shared_pdf_overview'))

        generated_extra_context = share_views.OverviewMixin.get_extra_context(response.wsgi_request)
        expected_extra_context = {
            'page': 'shared_pdf_overview',
            'current_collection_id': str(self.user.id),
            'current_collection_name': 'Default',
            'current_workspace_id': str(self.user.id),
        }

        self.assertEqual(generated_extra_context, expected_extra_context)


class TestCollectionOverviewMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)

        # create some pdfs
        for i in range(1, 4):
            SharedCollection.objects.create(collection=self.user.profile.current_collection, name=f'shared_{i}')

        deletion_date = datetime.now(timezone.utc) - timedelta(minutes=5)
        SharedCollection.objects.create(
            collection=self.user.profile.current_collection, name='shared_deleted', deletion_date=deletion_date
        )

    def test_filter_objects(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(f'{reverse('shared_collection_overview')}?q=pdf_2+%23tag_2')

        # make sure only current shared collections are returned
        other_ws = create_workspace('other_ws', creator=self.user)
        SharedCollection.objects.create(collection=other_ws.collections.first(), name='other_share')

        filtered_shares = CollectionOverviewMixin.filter_objects(response.wsgi_request)
        shared_names = [shared.name for shared in filtered_shares]

        self.assertEqual(shared_names, ['shared_1', 'shared_2', 'shared_3'])

    def test_get_extra_context(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('shared_pdf_overview'))

        generated_extra_context = share_views.CollectionOverviewMixin.get_extra_context(response.wsgi_request)
        expected_extra_context = {
            'page': 'shared_collection_overview',
            'current_collection_id': str(self.user.id),
            'current_collection_name': 'Default',
            'current_workspace_id': str(self.user.id),
        }

        self.assertEqual(generated_extra_context, expected_extra_context)


class TestSharedPdfMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)

    def test_get_object(self):
        self.client.login(username=self.username, password=self.password)
        # we need to create a request so get_pdf can access the user profile
        response = self.client.get(reverse('pdf_overview'))

        # make sure we can access shared pdf of non active
        other_ws = create_workspace('other_ws', creator=self.user)
        other_ws_pdf = Pdf.objects.create(collection=other_ws.collections[0], name='other_ws_pdf')
        other_shared_pdf = SharedPdf.objects.create(pdf=other_ws_pdf, name='other_share')

        self.assertNotEqual(other_ws, self.user.profile.current_workspace)
        self.assertEqual(other_shared_pdf, SharedPdfMixin.get_object(response.wsgi_request, other_shared_pdf.id))


class TestSharedCollectionMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)

    def test_get_object(self):
        self.client.login(username=self.username, password=self.password)
        # we need to create a request so get_pdf can access the user profile
        response = self.client.get(reverse('pdf_overview'))

        # make sure we can access shared collection of non active
        other_ws = create_workspace('other_ws', creator=self.user)
        collection = other_ws.collections.first()
        other_shared = SharedCollection.objects.create(collection=collection, name='other_share')

        self.assertNotEqual(other_ws, self.user.profile.current_workspace)
        self.assertEqual(other_shared, SharedCollectionMixin.get_object(response.wsgi_request, other_shared.id))


class TestEditSharedPdfMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)
        self.shared_pdf = SharedPdf.objects.create(pdf=self.pdf, name='share')

    def test_get_edit_form_get(self):
        shared_pdf = SharedPdf.objects.create(pdf=self.pdf, name='share', max_views=4)

        edit_pdf_mixin_object = EditSharedPdfMixin()

        for field, form_class, field_value in zip(
            ['name', 'max_views', 'password', 'deletion_date'],
            [
                SharedNameForm,
                SharedMaxViewsForm,
                SharedPasswordForm,
                SharedDeletionDateForm,
            ],
            ['share', 4, '', ''],
        ):
            form = edit_pdf_mixin_object.get_edit_form_get(field, shared_pdf)
            self.assertIsInstance(form, form_class)
            self.assertEqual(form.initial, {field: field_value})

    def test_process_field_changed_field(self):
        EditSharedPdfMixin.process_field('deletion_date', self.shared_pdf, None, {'deletion_input': '1d0h22m'})
        adjusted_shared_pdf = self.user.profile.current_shared_pdfs.get(name='share')

        for generated_result in [adjusted_shared_pdf.deletion_date]:
            expected_result = datetime.now(timezone.utc) + timedelta(days=1, hours=0, minutes=22)

            self.assertTrue((generated_result - expected_result).total_seconds() < 0.1)

    def test_process_field_unchanged_field(self):
        EditSharedPdfMixin.process_field('other', self.shared_pdf, None, {})
        adjusted_shared_pdf = self.user.profile.current_shared_pdfs.get(name='share')

        self.assertEqual(self.shared_pdf, adjusted_shared_pdf)

    def test_process_field_name(self):
        self.client.login(username=self.username, password=self.password)
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))

        EditSharedPdfMixin.process_field('name', self.shared_pdf, response.wsgi_request, {'name': 'new name '})
        adjusted_shared_pdf = self.user.profile.current_shared_pdfs.get(id=self.shared_pdf.id)

        # also make sure space was stripped
        self.assertEqual(adjusted_shared_pdf.name, 'new name')

    def test_process_field_name_existing(self):
        self.client.login(username=self.username, password=self.password)
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        shared_pdf_2 = SharedPdf.objects.create(pdf=self.pdf, name='shared_2')
        request = response.wsgi_request

        EditSharedPdfMixin.process_field('name', self.shared_pdf, request, {'name': shared_pdf_2.name})

        messages = get_messages(request)

        self.assertEqual(len(messages), 1)
        self.assertEqual(list(messages)[0].message, 'This name is already used by another shared PDF!')
        changed_shared_pdf = SharedPdf.objects.get(id=self.shared_pdf.id)
        self.assertEqual(changed_shared_pdf.name, 'share')


class TestEditSharedCollectionMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)
        self.shared_collection = SharedCollection.objects.create(
            collection=self.user.profile.current_collection, name='share'
        )

    def test_get_edit_form_get(self):
        edit_collection_mixin_object = EditSharedCollectionMixin()

        for field, form_class, field_value in zip(
            ['name', 'password', 'deletion_date'],
            [
                SharedNameForm,
                SharedPasswordForm,
                SharedDeletionDateForm,
            ],
            ['share', '', ''],
        ):
            form = edit_collection_mixin_object.get_edit_form_get(field, self.shared_collection)
            self.assertIsInstance(form, form_class)
            self.assertEqual(form.initial, {field: field_value})

    def test_process_field_changed_field(self):
        EditSharedCollectionMixin.process_field(
            'deletion_date', self.shared_collection, None, {'deletion_input': '1d0h22m'}
        )
        adjusted_shared_collection = self.user.profile.all_shared_collections.get(name='share')

        for generated_result in [adjusted_shared_collection.deletion_date]:
            expected_result = datetime.now(timezone.utc) + timedelta(days=1, hours=0, minutes=22)

            self.assertTrue((generated_result - expected_result).total_seconds() < 0.1)

    def test_process_field_unchanged_field(self):
        EditSharedCollectionMixin.process_field('other', self.shared_collection, None, {})
        adjusted_shared_collection = self.user.profile.all_shared_collections.get(name='share')

        self.assertEqual(self.shared_collection, adjusted_shared_collection)

    def test_process_field_name(self):
        self.client.login(username=self.username, password=self.password)
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))

        EditSharedCollectionMixin.process_field(
            'name', self.shared_collection, response.wsgi_request, {'name': 'new name '}
        )
        adjusted_shared_collection = self.user.profile.all_shared_collections.get(id=self.shared_collection.id)

        # also make sure space was stripped
        self.assertEqual(adjusted_shared_collection.name, 'new name')

    def test_process_field_name_existing(self):
        self.client.login(username=self.username, password=self.password)
        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        shared_collection_2 = SharedCollection.objects.create(
            collection=self.user.profile.current_collection, name='shared_2'
        )
        request = response.wsgi_request

        EditSharedCollectionMixin.process_field(
            'name', self.shared_collection, request, {'name': shared_collection_2.name}
        )

        messages = get_messages(request)

        self.assertEqual(len(messages), 1)
        self.assertEqual(list(messages)[0].message, 'This name is already used by another shared collection!')
        changed_shared_collection = SharedCollection.objects.get(id=self.shared_collection.id)
        self.assertEqual(changed_shared_collection.name, 'share')


class TestPdfPublicMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)

    @patch('pdf.services.shared_services.check_shared_access_allowed', return_value=True)
    def test_get_object(self, mock_check):
        # get dummy request
        response = self.client.get(reverse('pdf_overview'))
        shared_pdf = SharedPdf.objects.create(pdf=self.pdf, name='share')

        self.assertEqual(shared_pdf.pdf, PdfPublicMixin.get_object(response.wsgi_request, shared_pdf.id))

    @patch('pdf.services.shared_services.check_shared_access_allowed', return_value=False)
    def test_get_object_404(self, mock_check):
        # get dummy request
        response = self.client.get(reverse('pdf_overview'))
        shared_pdf = SharedPdf.objects.create(pdf=self.pdf, name='share')

        with pytest.raises(Http404, match='Access to shared pdf not allowed!'):
            PdfPublicMixin.get_object(response.wsgi_request, shared_pdf.id)


class TestCollectionPdfPublicMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)

    @patch('pdf.services.shared_services.check_shared_access_allowed', return_value=True)
    def test_get_object(self, mock_check):
        # get dummy request
        request = self.client.get(reverse('pdf_overview')).wsgi_request
        request.GET = MagicMock()
        request.GET.get.return_value = self.pdf.id
        shared_collection = SharedCollection.objects.create(collection=self.pdf.collection, name='share')

        self.assertEqual(self.pdf, CollectionPdfPublicMixin.get_object(request, shared_collection.id))

    @patch('pdf.services.shared_services.check_shared_access_allowed', return_value=False)
    def test_get_object_404(self, mock_check):
        # get dummy request
        request = self.client.get(reverse('pdf_overview')).wsgi_request
        shared_collection = SharedCollection.objects.create(collection=self.pdf.collection, name='share')

        with pytest.raises(Http404, match='Access to shared collection not allowed!'):
            CollectionPdfPublicMixin.get_object(request, shared_collection.id)


class TestSharedPdfPublicView(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)

    def test_get_shared_obj_public(self):
        shared_pdf = SharedPdf.objects.create(pdf=self.pdf, name='share')

        self.assertEqual(shared_pdf, SharedPdfPublicView.get_shared_obj_public(None, shared_pdf.id))


class TestSharedCollectionPublicView(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)

    def test_get_shared_obj_public(self):
        shared_collection = SharedCollection.objects.create(
            collection=self.user.profile.current_collection, name='share'
        )

        self.assertEqual(
            shared_collection, SharedCollectionPublicView.get_shared_obj_public(None, shared_collection.id)
        )


class TestBasePublicView(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        set_up(self)
        self.shared_pdf = SharedPdf.objects.create(pdf=self.pdf, name='shared_pdf')

    @patch('pdf.views.share_views.check_shared_access_allowed', return_value=False)
    def test_view_get_active_no_active_session(self, mock_check):
        # test without http referer
        response = self.client.get(reverse('view_shared_pdf', kwargs={'identifier': self.shared_pdf.id}))

        self.assertTemplateUsed(response, 'view_shared_info.html')
        self.assertEqual(response.context['shared_obj'], self.shared_pdf)
        self.assertEqual(response.context['form'], ViewSharedPasswordForm)

    @patch('pdf.views.share_views.get_viewer_theme_and_color')
    @patch('pdf.views.share_views.check_shared_access_allowed', return_value=True)
    def test_view_get_active_active_session(self, mock_check, mock_get_viewer_theme_and_color):
        # test without http referer

        mock_get_viewer_theme_and_color.return_value = 'dark', '4 4 4'
        self.shared_pdf.pdf.revision = 2
        self.shared_pdf.pdf.save()
        self.assertEqual(self.shared_pdf.views, 0)

        response = self.client.get(reverse('view_shared_pdf', kwargs={'identifier': self.shared_pdf.id}))
        self.assertEqual(response.context['shared_pdf_id'], self.shared_pdf.id)
        self.assertEqual(response.context['current_page'], 1)
        self.assertEqual(response.context['revision'], 2)
        self.assertEqual(response.context['theme_color'], '4 4 4')
        self.assertEqual(response.context['theme'], 'dark')
        self.assertEqual(response.context['tab_title'], 'PdfDing')
        self.assertEqual(response.context['user_view_bool'], False)
        self.assertTemplateUsed(response, 'viewer.html')

        shared_pdf = SharedPdf.objects.get(pk=self.shared_pdf.id)
        self.assertEqual(shared_pdf.views, 1)

    @patch('pdf.views.share_views.get_viewer_theme_and_color')
    @patch('pdf.views.share_views.check_shared_access_allowed', return_value=True)
    def test_view_get_active_active_session_collection(self, mock_check, mock_get_viewer_theme_and_color):
        mock_get_viewer_theme_and_color.return_value = 'dark', '4 4 4'
        shared_collection = SharedCollection.objects.create(
            collection=self.user.profile.current_collection, name='shared_collection'
        )

        response = self.client.get(reverse('view_shared_collection', kwargs={'identifier': shared_collection.id}))
        self.assertEqual(response.context['collection_name'], shared_collection.collection.name)
        self.assertEqual(response.context['shared_collection_id'], shared_collection.id)
        for pdf_1, pdf_2 in zip(
            response.context['pdfs'], self.user.profile.current_collection.pdfs.order_by('-creation_date')
        ):
            assert pdf_1 == pdf_2
        self.assertTemplateUsed(response, 'public_shared_collection_overview.html')

    @patch('pdf.views.share_views.get_viewer_theme_and_color')
    @patch('pdf.views.share_views.check_shared_access_allowed', return_value=True)
    def test_view_get_active_active_session_collection_pdf(self, mock_check, mock_get_viewer_theme_and_color):
        mock_get_viewer_theme_and_color.return_value = 'dark', '4 4 4'
        self.pdf.revision = 2
        self.pdf.save()
        shared_collection = SharedCollection.objects.create(
            collection=self.user.profile.current_collection, name='shared_collection'
        )

        response = self.client.get(
            f'{reverse('view_shared_collection', kwargs={'identifier': shared_collection.id})}?pdf={self.pdf.id}'
        )
        self.assertEqual(response.context['current_page'], 1)
        self.assertEqual(response.context['shared_collection_id'], shared_collection.id)
        self.assertEqual(response.context['pdf_id'], self.pdf.id)
        self.assertEqual(response.context['revision'], 2)
        self.assertEqual(response.context['theme_color'], '4 4 4')
        self.assertEqual(response.context['theme'], 'dark')
        self.assertEqual(response.context['tab_title'], 'PdfDing')
        self.assertEqual(response.context['user_view_bool'], False)
        self.assertTemplateUsed(response, 'viewer.html')

    def test_view_get_inactive(self):
        inactive_shared_pdf = SharedPdf.objects.create(pdf=self.pdf, name='inactive_shared_pdf', views=2, max_views=1)
        response = self.client.get(reverse('view_shared_pdf', kwargs={'identifier': inactive_shared_pdf.id}))

        self.assertTemplateUsed(response, 'view_shared_inactive.html')

    def test_view_post_active_no_password(self):
        unprotected_shared_pdf = SharedPdf.objects.create(pdf=self.pdf, name='unprotected_shared_pdf')
        assert unprotected_shared_pdf.sessions.count() == 0

        response = self.client.post(reverse('view_shared_pdf', kwargs={'identifier': unprotected_shared_pdf.id}))

        assert unprotected_shared_pdf.sessions.count() == 1
        self.assertRedirects(response, reverse('view_shared_pdf', kwargs={'identifier': unprotected_shared_pdf.id}))

    def test_view_post_active_wrong_password(self):
        protected_shared_pdf = SharedPdf.objects.create(
            pdf=self.pdf, name='protected_shared_pdf', password=make_password('some_pw')
        )

        response = self.client.post(
            reverse('view_shared_pdf', kwargs={'identifier': protected_shared_pdf.id}), data={'password_input': 'wrong'}
        )

        self.assertIsInstance(response.context['form'], ViewSharedPasswordForm)
        self.assertTemplateUsed(response, 'view_shared_info.html')

    def test_view_post_active_correct_password(self):
        protected_shared_pdf = SharedPdf.objects.create(
            pdf=self.pdf, name='protected_shared_pdf', password=make_password('some_pw')
        )
        assert protected_shared_pdf.sessions.count() == 0

        response = self.client.post(
            reverse('view_shared_pdf', kwargs={'identifier': protected_shared_pdf.id}),
            data={'password_input': 'some_pw'},
        )

        assert protected_shared_pdf.sessions.count() == 1
        self.assertRedirects(response, reverse('view_shared_pdf', kwargs={'identifier': protected_shared_pdf.id}))

    def test_view_post_inactive(self):
        inactive_shared_pdf = SharedPdf.objects.create(pdf=self.pdf, name='inactive_shared_pdf', views=2, max_views=1)
        response = self.client.post(reverse('view_shared_pdf', kwargs={'identifier': inactive_shared_pdf.id}))

        self.assertTemplateUsed(response, 'view_shared_inactive.html')

    def test_view_post_deleted(self):
        deleted_shared_pdf = SharedPdf.objects.create(
            pdf=self.pdf, name='inactive_shared_pdf', deletion_date=(datetime.now(timezone.utc) - timedelta(minutes=5))
        )
        response = self.client.post(reverse('view_shared_pdf', kwargs={'identifier': deleted_shared_pdf.id}))

        self.assertTemplateUsed(response, 'view_shared_inactive.html')
