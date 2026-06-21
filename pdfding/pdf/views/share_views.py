from abc import abstractmethod
from datetime import datetime, timezone
from io import BytesIO

import qrcode
from base import base_views
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.contrib.sessions.models import Session
from django.core.files import File
from django.db.models import Q, QuerySet
from django.db.models.functions import Lower
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
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
from pdf.services.pdf_services import check_object_access_allowed
from pdf.services.shared_services import (
    check_shared_access_allowed,
    check_shared_collection_access_allowed_by_identifier,
    check_shared_pdf_access_allowed_by_identifier,
    get_future_datetime,
)
from pdf.services.workspace_services import get_shared_collections_of_workspace, get_shared_pdfs_of_workspace
from pdf.views.collection_views import CollectionMixin
from pdf.views.pdf_views import PdfMixin
from qrcode.image import svg
from users.service import get_viewer_theme_and_color


class BaseShareMixin:
    obj_name = 'shared_pdf'


class BaseShareCollectionMixin:
    obj_name = 'shared_collection'


class BaseAddSharedMixin:
    template_name: str

    @staticmethod
    def generate_qr_code(qr_code_content: str) -> BytesIO:  # pragma: no cover
        """
        Create a qr code and return as a Bytes object.
        """

        qr = qrcode.QRCode(image_factory=svg.SvgPathImage, box_size=12, border=1)
        qr.add_data(qr_code_content)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        # save as bytes object so django can use it as a file for file field
        qr_as_byte = BytesIO()
        qr_img.save(qr_as_byte)

        return qr_as_byte

    @classmethod
    def add_qr_code(cls, shared_obj: SharedPdf | SharedCollection, reverse_url_name: str, request: HttpRequest) -> None:
        """Add the QR code to the shared object."""

        qr_code_content = (
            f'{request.scheme}://{request.get_host()}{reverse(reverse_url_name, kwargs={"identifier": shared_obj.id})}'
        )
        qr_as_byte = cls.generate_qr_code(qr_code_content)

        shared_obj.file.save(None, File(qr_as_byte))

    @staticmethod
    def set_access_dates(shared_obj: SharedPdf | SharedCollection, deletion_input: str) -> None:
        """Set the deletion date of the shared object."""

        if deletion_input:
            shared_obj.deletion_date = get_future_datetime(deletion_input)

        shared_obj.save()


class AddSharedPdfMixin(BaseAddSharedMixin, BaseShareMixin):
    form = ShareForm
    template_name = 'add_shared_pdf.html'

    def get_context_get(self, request: HttpRequest, pdf_id: str):
        """Get the context needed to be passed to the template containing the form for adding a shared PDF."""

        pdf = PdfMixin.get_object(request, pdf_id)
        form = self.form

        context = {'form': form(profile=request.user.profile), 'pdf_name': pdf.name}

        return context

    @classmethod
    def obj_save(cls, form: ShareForm, request: HttpRequest, identifier: str):
        """Save the shared PDF based on the submitted form."""

        shared_pdf = form.save(commit=False)
        shared_pdf.pdf = PdfMixin.get_object(request, identifier)

        cls.add_qr_code(shared_pdf, 'view_shared_pdf', request)
        cls.set_access_dates(shared_pdf, form.data.get('deletion_input'))


class AddSharedCollectionMixin(BaseAddSharedMixin, BaseShareCollectionMixin):
    form = ShareCollectionForm
    template_name = 'add_shared_collection.html'

    def get_context_get(self, request: HttpRequest, pdf_id: str):
        """
        Get the context needed to be passed to the template containing the form for
        adding a shared collection.
        """

        collection = CollectionMixin.get_object(request, pdf_id)
        form = self.form

        context = {'form': form(profile=request.user.profile), 'collection_name': collection.name}

        return context

    @classmethod
    def obj_save(cls, form: ShareForm, request: HttpRequest, identifier: str):
        """Save the shared collection based on the submitted form."""

        shared_collection = form.save(commit=False)
        shared_collection.collection = CollectionMixin.get_object(request, identifier)

        cls.add_qr_code(shared_collection, 'view_shared_collection', request)
        cls.set_access_dates(shared_collection, form.data.get('deletion_input'))


class BaseOverviewMixin(BaseShareMixin):
    overview_page_name = 'shared_overview/overview_page'

    @staticmethod
    def get_sorting(request: HttpRequest):
        """Get the sorting of the overview page."""

        profile = request.user.profile

        sorting_dict = {
            'Newest': '-creation_date',
            'Oldest': 'creation_date',
            'Name_asc': Lower('name'),
            'Name_desc': Lower('name').desc(),
        }

        return sorting_dict[profile.shared_pdf_sorting]


class OverviewMixin(BaseOverviewMixin):
    overview_name = 'shared_overview'

    @staticmethod
    def filter_objects(request: HttpRequest) -> QuerySet:
        """
        Filter the shared PDFs when performing a search in the overview. As there is no search functionality, this is
        just a dummy function
        """

        shared_pdfs = request.user.profile.current_shared_pdfs
        shared_pdfs = shared_pdfs.filter(
            Q(deletion_date__isnull=True) | Q(deletion_date__gt=datetime.now(timezone.utc))
        )

        return shared_pdfs

    @staticmethod
    def get_extra_context(request: HttpRequest) -> dict:
        """get further information that needs to be passed to the template."""

        return {
            'page': 'shared_pdf_overview',
            'current_collection_id': request.user.profile.current_collection_id,
            'current_collection_name': request.user.profile.current_collection_name,
            'current_workspace_id': request.user.profile.current_workspace_id,
        }


class CollectionOverviewMixin(BaseOverviewMixin):
    overview_name = 'shared_overview'

    @staticmethod
    def filter_objects(request: HttpRequest) -> QuerySet:
        """
        Filter the shared collections when performing a search in the overview. As there is no search
        functionality, this is just a dummy function.
        """

        shared_collections = get_shared_collections_of_workspace(request.user.profile.current_workspace)
        shared_collections = shared_collections.filter(
            Q(deletion_date__isnull=True) | Q(deletion_date__gt=datetime.now(timezone.utc))
        )

        return shared_collections

    @staticmethod
    def get_extra_context(request: HttpRequest) -> dict:
        """get further information that needs to be passed to the template."""

        return {
            'page': 'shared_collection_overview',
            'current_collection_id': request.user.profile.current_collection_id,
            'current_collection_name': request.user.profile.current_collection_name,
            'current_workspace_id': request.user.profile.current_workspace_id,
        }


class SharedPdfMixin(BaseShareMixin):
    obj_class = SharedPdf

    @staticmethod
    @check_object_access_allowed
    def get_object(request: HttpRequest, identifier: str):
        """Get the shared pdf specified by the ID"""

        user_profile = request.user.profile
        shared_pdf = user_profile.all_shared_pdfs.get(id=identifier)

        return shared_pdf


class SharedCollectionMixin(BaseShareCollectionMixin):
    obj_class = SharedCollection

    @staticmethod
    @check_object_access_allowed
    def get_object(request: HttpRequest, identifier: str):
        """Get the shared pdf specified by the ID"""

        user_profile = request.user.profile
        shared_collection = user_profile.all_shared_collections.get(id=identifier)

        return shared_collection


class EditSharedPdfMixin(SharedPdfMixin):
    fields_requiring_extra_processing = ['deletion_date', 'name']

    @staticmethod
    def get_edit_form_dict():
        """Get the forms of the fields that can be edited as a dict."""

        form_dict = {
            'name': SharedNameForm,
            'max_views': SharedMaxViewsForm,
            'password': SharedPasswordForm,
            'deletion_date': SharedDeletionDateForm,
        }

        return form_dict

    def get_edit_form_get(self, field_name: str, shared_pdf: SharedPdf):
        """Get the form belonging to the specified field."""

        form_dict = self.get_edit_form_dict()

        initial_dict = {
            'name': {'name': shared_pdf.name},
            'max_views': {'max_views': shared_pdf.max_views},
            'password': {'password': ''},  # nosec B105
            'deletion_date': {'deletion_date': ''},
        }

        form = form_dict[field_name](initial=initial_dict[field_name])

        return form

    @classmethod
    def process_field(cls, field_name: str, shared_pdf: SharedPdf, request: HttpRequest, form_data: dict):
        """Process fields that are not covered in the base edit view."""

        if field_name == 'deletion_date':
            shared_pdf.deletion_date = get_future_datetime(form_data['deletion_input'])
            shared_pdf.save()
        elif field_name == 'name':
            shared_pdfs = get_shared_pdfs_of_workspace(request.user.profile.current_workspace)
            existing_obj = shared_pdfs.filter(name__iexact=form_data.get('name')).first()

            if existing_obj and str(existing_obj.id) != str(shared_pdf.id):
                messages.warning(request, _('This name is already used by another shared PDF!'))
            else:
                shared_pdf.name = form_data.get('name').strip()
                shared_pdf.save()


class EditSharedCollectionMixin(SharedCollectionMixin):
    fields_requiring_extra_processing = ['deletion_date', 'name']

    @staticmethod
    def get_edit_form_dict():
        """Get the forms of the fields that can be edited as a dict."""

        form_dict = {
            'name': SharedNameForm,
            'password': SharedPasswordForm,
            'deletion_date': SharedDeletionDateForm,
        }

        return form_dict

    def get_edit_form_get(self, field_name: str, shared_collection: SharedCollection):
        """Get the form belonging to the specified field."""

        form_dict = self.get_edit_form_dict()

        initial_dict = {
            'name': {'name': shared_collection.name},
            'password': {'password': ''},  # nosec B105
            'deletion_date': {'deletion_date': ''},
        }

        form = form_dict[field_name](initial=initial_dict[field_name])

        return form

    @classmethod
    def process_field(cls, field_name: str, shared_collection: SharedCollection, request: HttpRequest, form_data: dict):
        """Process fields that are not covered in the base edit view."""

        if field_name == 'deletion_date':
            shared_collection.deletion_date = get_future_datetime(form_data['deletion_input'])
            shared_collection.save()
        elif field_name == 'name':
            shared_collections = get_shared_collections_of_workspace(request.user.profile.current_workspace)
            existing_obj = shared_collections.filter(name__iexact=form_data.get('name')).first()

            if existing_obj and str(existing_obj.id) != str(shared_collection.id):
                messages.warning(request, _('This name is already used by another shared collection!'))
            else:
                shared_collection.name = form_data.get('name').strip()
                shared_collection.save()


class PdfPublicMixin:
    @staticmethod
    def get_object(request: HttpRequest, shared_id: str):
        """Get the shared pdf specified by the ID"""

        if check_shared_pdf_access_allowed_by_identifier(shared_id, request.session):
            shared_pdf = SharedPdf.objects.get(pk=shared_id)

            return shared_pdf.pdf
        else:
            raise Http404('Access to shared pdf not allowed!')


class CollectionPdfPublicMixin:
    @staticmethod
    @check_object_access_allowed
    def get_object(request: HttpRequest, shared_id: str):
        """Get the pdf of a shared pdf specified by the ID"""

        # as I do not want to rewrite the existing logic I kind of abuse it instead
        pdf_id = request.GET.get('pdf', None)

        if check_shared_collection_access_allowed_by_identifier(shared_id, request.session):
            shared_collection = SharedCollection.objects.get(pk=shared_id)
            pdf = shared_collection.collection.pdfs.get(id=pdf_id)

            return pdf
        else:
            raise Http404('Access to shared collection not allowed!')


class Share(AddSharedPdfMixin, base_views.BaseAdd):
    """View for sharing PDF files."""


class ShareCollection(AddSharedCollectionMixin, base_views.BaseAdd):
    """View for sharing collections."""


class Overview(OverviewMixin, base_views.BaseOverview):
    """
    View for the shared PDF overview page. It's also responsible for paginating the shared PDFs.
    """


class CollectionOverview(CollectionOverviewMixin, base_views.BaseOverview):
    """
    View for the shared collection overview page. It's also responsible for paginating the shared collections.
    """


class OverviewQuery(BaseShareMixin, base_views.BaseOverviewQuery):
    """View for performing searches and sorting on the shared PDF overview page."""


class CollectionOverviewQuery(BaseShareCollectionMixin, base_views.BaseOverviewQuery):
    """View for performing searches and sorting on the shared PDF overview page."""


class Delete(SharedPdfMixin, base_views.BaseDelete):
    """View for deleting the shared PDF specified by its ID."""


class DeleteSharedCollection(SharedCollectionMixin, base_views.BaseDelete):
    """View for deleting the shared PDF specified by its ID."""


class Edit(EditSharedPdfMixin, base_views.BaseDetailsEdit):
    """
    The view for editing a shared PDF's name. The field, that is to be changed, is specified by the
    'field' argument.
    """


class EditSharedCollection(EditSharedCollectionMixin, base_views.BaseDetailsEdit):
    """
    The view for editing a shared collection's name. The field, that is to be changed, is specified by the
    'field' argument.
    """


class Details(SharedPdfMixin, base_views.BaseDetails):
    """View for displaying the details page of a shared PDF."""


class DetailsSharedCollection(SharedCollectionMixin, base_views.BaseDetails):
    """View for displaying the details page of a shared collection."""


class ServeQrCode(SharedPdfMixin, base_views.BaseServe):
    """View used for serving the qr code of a shared PDF files specified by its id."""


class ServeSharedCollectionQrCode(SharedCollectionMixin, base_views.BaseServe):
    """View used for serving the qr code of a shared collection specified by its id."""


class DownloadQrCode(SharedPdfMixin, base_views.BaseDownload):
    """View used for downloading the qr code of a shared PDF files specified by its id."""

    @staticmethod
    def get_suffix():  # pragma: no cover
        """
        Return svg suffix
        """

        return '.svg'


class DownloadSharedCollectionQrCode(SharedCollectionMixin, base_views.BaseDownload):
    """View used for downloading the qr code of a shared collection specified by its id."""

    @staticmethod
    def get_suffix():  # pragma: no cover
        """
        Return svg suffix
        """

        return '.svg'


@method_decorator(login_not_required, name="dispatch")
class Serve(PdfPublicMixin, base_views.BaseServe):
    """View used for serving shared PDF files."""


@method_decorator(login_not_required, name="dispatch")
class ServeCollectionPdf(CollectionPdfPublicMixin, base_views.BaseServe):
    """View used for serving PDF files of a shared collection."""


@method_decorator(login_not_required, name="dispatch")
class Download(PdfPublicMixin, base_views.BaseDownload):
    """View for downloading the PDF specified by the ID."""


@method_decorator(login_not_required, name="dispatch")
class DownloadCollectionPdf(CollectionPdfPublicMixin, base_views.BaseDownload):
    """View for downloading the collection pdf specified by the ID."""


@method_decorator(login_not_required, name="dispatch")
class BasePublicViewShared(View):
    """The view responsible for displaying the shared PDF file specified by the shared PDF id in the browser."""

    view_name: str

    def get(self, request: HttpRequest, identifier: str):
        shared_obj = self.get_shared_obj_public(request, identifier)
        secondary_identifier = request.GET.get('pdf', None)

        if shared_obj.inactive or shared_obj.deleted:
            return render(request, 'view_shared_inactive.html')
        elif check_shared_access_allowed(shared_obj, request.session):
            return self.render_shared_obj(request, shared_obj, secondary_identifier)
        else:
            return render(
                request,
                'view_shared_info.html',
                {
                    'shared_obj': shared_obj,
                    'shared_class': shared_obj.__class__.__name__,
                    'form': ViewSharedPasswordForm,
                },
            )

    def post(self, request: HttpRequest, identifier: str):
        shared_obj = self.get_shared_obj_public(request, identifier)

        if shared_obj.inactive or shared_obj.deleted:
            return render(request, 'view_shared_inactive.html')
        else:
            form = ViewSharedPasswordForm(request.POST, shared_obj=shared_obj)

            if not shared_obj.password or form.is_valid():
                if not request.session or not request.session.session_key:
                    request.session.create()
                    # set session expiry to 1 week
                    request.session.set_expiry(604800)
                    request.session.save()

                shared_obj.sessions.add(Session.objects.get(session_key=request.session.session_key))
                return redirect(self.view_name, identifier=shared_obj.id)
            else:
                return render(
                    request,
                    'view_shared_info.html',
                    {'shared_obj': shared_obj, 'shared_class': shared_obj.__class__.__name__, 'form': form},
                )

    @staticmethod
    @abstractmethod
    @check_object_access_allowed
    def get_shared_obj_public(request: HttpRequest, shared_id: str) -> SharedPdf | SharedCollection:
        """Get the shared object specified by the ID without being logged in."""
        # first parameter needed because of the decorator

    @classmethod
    @abstractmethod
    def render_shared_obj(cls, request: HttpRequest, shared_obj, secondary_identifier: str) -> HttpResponse:
        """Render the shared obj, e.g. view the  shared PDF"""


class SharedPdfPublicView(BasePublicViewShared):
    view_name = 'view_shared_pdf'

    @staticmethod
    @check_object_access_allowed
    # first parameter needed because of the decorator
    def get_shared_obj_public(request: HttpRequest, shared_id: str) -> SharedPdf:
        """Get the shared pdf specified by the ID without being logged in."""

        shared_pdf = SharedPdf.objects.get(pk=shared_id)

        return shared_pdf

    @classmethod
    def render_shared_obj(cls, request: HttpRequest, shared_obj: SharedPdf, secondary_identifier: str) -> HttpResponse:
        """Render the shared PDF."""

        shared_obj.views += 1
        shared_obj.save()

        theme, theme_color = get_viewer_theme_and_color()

        return render(
            request,
            'viewer.html',
            {
                'tab_title': 'PdfDing',
                'current_page': 1,
                'shared_pdf_id': shared_obj.id,
                'revision': shared_obj.pdf.revision,
                'theme': theme,
                'theme_color': theme_color,
                'user_view_bool': False,
            },
        )


class SharedCollectionPublicView(BasePublicViewShared):
    view_name = 'view_shared_collection'

    @staticmethod
    @check_object_access_allowed
    # first parameter needed because of the decorator
    def get_shared_obj_public(request: HttpRequest, shared_id: str) -> SharedCollection:
        """Get the shared collection specified by the ID without being logged in."""

        shared_collection = SharedCollection.objects.get(pk=shared_id)

        return shared_collection

    # This function kinda abuses the check_object_access_allowed function but I still use it as
    # I do not want to repeat the logic
    @staticmethod
    @check_object_access_allowed
    def get_pdf_public(shared_collection, pdf_id: str) -> Pdf:
        """Gets the pdf of a shared collection."""

        pdf = shared_collection.collection.pdfs.get(id=pdf_id)

        return pdf

    @classmethod
    def render_shared_obj(
        cls, request: HttpRequest, shared_obj: SharedCollection, secondary_identifier: str
    ) -> HttpResponse:
        """
        Render the shared collection or one of its PDFs. If a secondary id is provided the PDF
        of a collection will be rendered.
        """

        # a pdf of a shared collection needs to be rendered
        if secondary_identifier:
            pdf = cls.get_pdf_public(shared_obj, secondary_identifier)

            theme, theme_color = get_viewer_theme_and_color()

            return render(
                request,
                'viewer.html',
                {
                    'tab_title': 'PdfDing',
                    'current_page': 1,
                    'shared_collection_id': shared_obj.id,
                    'pdf_id': pdf.id,
                    'revision': pdf.revision,
                    'theme': theme,
                    'theme_color': theme_color,
                    'user_view_bool': False,
                },
            )
        # a shared collection needs to be rendered
        else:
            return render(
                request,
                'public_shared_collection_overview.html',
                {
                    'collection_name': shared_obj.collection.name,
                    'shared_collection_id': shared_obj.id,
                    'pdfs': shared_obj.collection.pdfs.order_by('-creation_date'),
                },
            )
