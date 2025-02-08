from datetime import datetime, timezone
from io import BytesIO

import qrcode
from base import base_views
from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.core.files import File
from django.db.models import Q, QuerySet
from django.db.models.functions import Lower
from django.http import HttpRequest
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from pdf.forms import (
    SharedDeletionDateForm,
    SharedDescriptionForm,
    SharedExpirationDateForm,
    SharedMaxViewsForm,
    SharedNameForm,
    SharedPasswordForm,
    ShareForm,
    ViewSharedPasswordForm,
)
from pdf.models import SharedPdf
from pdf.service import check_object_access_allowed, get_future_datetime
from pdf.views.pdf_views import PdfMixin
from qrcode.image import svg


class BaseShareMixin:
    obj_name = 'shared_pdf'


class AddSharedPdfMixin(BaseShareMixin):
    form = ShareForm
    template_name = 'add_shared_pdf.html'

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

    def get_context_get(self, request: HttpRequest, pdf_id: str):
        """Get the context needed to be passed to the template containing the form for adding a shared PDf."""

        pdf = PdfMixin.get_object(request, pdf_id)
        form = self.form

        context = {'form': form, 'pdf_name': pdf.name}

        return context

    @classmethod
    def obj_save(cls, form: ShareForm, request: HttpRequest, identifier: str):
        """Save the shared PDF based on the submitted form."""

        shared_pdf = form.save(commit=False)
        shared_pdf.owner = request.user.profile
        shared_pdf.pdf = PdfMixin.get_object(request, identifier)

        cls.add_qr_code(shared_pdf, request)
        cls.set_access_dates(shared_pdf, form.data.get('expiration_input'), form.data.get('deletion_input'))

    @classmethod
    def add_qr_code(cls, shared_pdf: SharedPdf, request: HttpRequest):
        """Add the QR code to the shared PDF."""

        qr_code_content = (
            f'{request.scheme}://{request.get_host()}{reverse("view_shared_pdf", kwargs={"identifier": shared_pdf.id})}'
        )
        qr_as_byte = cls.generate_qr_code(qr_code_content)

        shared_pdf.file.save(None, File(qr_as_byte))

    @staticmethod
    def set_access_dates(shared_pdf, expiration_input, deletion_input):
        """Set the deletion date and expiration date of the shared PDF."""

        if expiration_input:
            shared_pdf.expiration_date = get_future_datetime(expiration_input)
        if deletion_input:
            shared_pdf.deletion_date = get_future_datetime(deletion_input)

        shared_pdf.save()


class OverviewMixin(BaseShareMixin):
    @staticmethod
    def get_sorting_dict():
        """
        Get the sorting dict which describes the sorting in the overview page.
        """

        sorting_dict = {
            '': '-creation_date',
            'newest': '-creation_date',
            'oldest': 'creation_date',
            'title_asc': Lower('name'),
            'title_desc': Lower('name').desc(),
            'least_viewed': 'views',
            'most_viewed': '-views',
        }

        return sorting_dict

    @staticmethod
    def filter_objects(request: HttpRequest) -> QuerySet:
        """
        Filter the shared PDFs when performing a search in the overview. As there is no search functionality, this is
        just a dummy function
        """

        shared_pdfs = SharedPdf.objects.filter(owner=request.user.profile).all()
        shared_pdfs = shared_pdfs.filter(
            Q(deletion_date__isnull=True) | Q(deletion_date__gt=datetime.now(timezone.utc))
        )

        return shared_pdfs

    @staticmethod
    def get_extra_context(_) -> dict:  # pragma: no cover
        """get further information that needs to be passed to the template."""

        return dict()


class SharedPdfMixin(BaseShareMixin):
    obj_class = SharedPdf

    @staticmethod
    @check_object_access_allowed
    def get_object(request: HttpRequest, identifier: str):
        """Get the shered pdf specified by the ID"""

        user_profile = request.user.profile
        shared_pdf = user_profile.sharedpdf_set.get(id=identifier)

        return shared_pdf


class EditSharedPdfMixin(SharedPdfMixin):
    fields_requiring_extra_processing = ['expiration_date', 'deletion_date']

    @staticmethod
    def get_edit_form_dict():
        """Get the forms of the fields that can be edited as a dict."""

        form_dict = {
            'description': SharedDescriptionForm,
            'name': SharedNameForm,
            'max_views': SharedMaxViewsForm,
            'password': SharedPasswordForm,
            'expiration_date': SharedExpirationDateForm,
            'deletion_date': SharedDeletionDateForm,
        }

        return form_dict

    def get_edit_form_get(self, field_name: str, shared_pdf: SharedPdf):
        """Get the form belonging to the specified field."""

        form_dict = self.get_edit_form_dict()

        initial_dict = {
            'name': {'name': shared_pdf.name},
            'description': {'description': shared_pdf.description},
            'max_views': {'max_views': shared_pdf.max_views},
            'password': {'password': ''},
            'expiration_date': {'expiration_date': ''},
            'deletion_date': {'deletion_date': ''},
        }

        form = form_dict[field_name](initial=initial_dict[field_name])

        return form

    @staticmethod
    def process_field(field_name, shared_pdf, _, form_data):
        """Process fields that are not covered in the base edit view."""

        if field_name == 'expiration_date':
            shared_pdf.expiration_date = get_future_datetime(form_data['expiration_input'])

        if field_name == 'deletion_date':
            shared_pdf.deletion_date = get_future_datetime(form_data['deletion_input'])

        shared_pdf.save()


class PdfPublicMixin:
    @staticmethod
    @check_object_access_allowed
    def get_object(_, shared_id: str):
        """Get the shared pdf specified by the ID"""

        shared_pdf = SharedPdf.objects.get(pk=shared_id)

        return shared_pdf.pdf


class BaseSharedPdfPublicView(View):
    @staticmethod
    @check_object_access_allowed
    # first parameter needed because of the decorator
    def get_shared_pdf_public(_, shared_id: str):
        """Get the shared pdf specified by the ID without being logged in."""

        shared_pdf = SharedPdf.objects.get(pk=shared_id)

        return shared_pdf


class Share(AddSharedPdfMixin, base_views.BaseAdd):
    """View for new shared PDF files."""


class Overview(OverviewMixin, base_views.BaseOverview):
    """
    View for the shared PDF overview page. It's also responsible for paginating the shared PDFs.
    """


class OverviewQuery(BaseShareMixin, base_views.BaseOverviewQuery):
    """View for performing searches and sorting on the shared PDF overview page."""


class Delete(SharedPdfMixin, base_views.BaseDelete):
    """View for deleting the shared PDF specified by its ID."""


class Edit(EditSharedPdfMixin, base_views.BaseDetailsEdit):
    """
    The view for editing a shared PDF's name and description. The field, that is to be changed, is specified by the
    'field' argument.
    """


class Details(SharedPdfMixin, base_views.BaseDetails):
    """View for displaying the details page of a shared PDF."""


class ServeQrCode(SharedPdfMixin, base_views.BaseServe):
    """View used for serving the qr code of a shared PDF files specified by the shared PDF id"""


class DownloadQrCode(SharedPdfMixin, base_views.BaseDownload):
    """View used for downloading the qr code of a shared PDF files specified by the shared PDF id"""

    @staticmethod
    def get_suffix():  # pragma: no cover
        """
        Return svg suffix
        """

        return '.svg'


@method_decorator(login_not_required, name="dispatch")
class Serve(PdfPublicMixin, base_views.BaseServe):
    """View used for serving shared PDF files specified by the shared PDF id"""


@method_decorator(login_not_required, name="dispatch")
class Download(PdfPublicMixin, base_views.BaseDownload):
    """View for downloading the PDF specified by the ID."""


@method_decorator(login_not_required, name="dispatch")
class ViewShared(BaseSharedPdfPublicView):
    """The view responsible for displaying the shared PDF file specified by the shared PDF id in the browser."""

    def get(self, request: HttpRequest, identifier: str):
        shared_pdf = self.get_shared_pdf_public(request, identifier)

        if shared_pdf.inactive or shared_pdf.deleted:
            return render(request, 'view_shared_inactive.html')
        else:
            return render(
                request,
                'view_shared_info.html',
                {'shared_pdf': shared_pdf, 'form': ViewSharedPasswordForm, 'host': request.get_host()},
            )

    def post(self, request: HttpRequest, identifier: str):
        shared_pdf = self.get_shared_pdf_public(request, identifier)

        if shared_pdf.inactive:
            return render(request, 'view_shared_inactive.html')
        else:
            if shared_pdf.password:
                form = ViewSharedPasswordForm(request.POST, shared_pdf=shared_pdf)

                if form.is_valid():
                    return self.render_shared_pdf_view(request, shared_pdf)
                else:
                    return render(request, 'view_shared_info.html', {'shared_pdf': shared_pdf, 'form': form})
            else:
                return self.render_shared_pdf_view(request, shared_pdf)

    @staticmethod
    def render_shared_pdf_view(request: HttpRequest, shared_pdf: SharedPdf):
        shared_pdf.views += 1
        shared_pdf.save()

        theme_color_rgb_dict = {
            'Green': '74 222 128',
            'Blue': '71 147 204',
            'Gray': '151 170 189',
            'Red': '248 113 113',
            'Pink': '218 123 147',
            'Orange': '255 203 133',
            'Brown': '158 154 145',
        }

        return render(
            request,
            'viewer.html',
            {
                'tab_title': 'PdfDing',
                'current_page': 1,
                'shared_pdf_id': shared_pdf.id,
                'revision': shared_pdf.pdf.revision,
                'theme_color_rgb': theme_color_rgb_dict[settings.DEFAULT_THEME_COLOR],
                'user_view_bool': False,
            },
        )
