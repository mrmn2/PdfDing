from base import base_views
from django.db.models import QuerySet
from django.db.models.functions import Lower
from django.http import HttpRequest
from pdf.forms import AddForm, DescriptionForm, NameForm
from pdf.models import Pdf


class BaseMixin:
    obj_name = 'pdf'


class BaseAddMixin(BaseMixin):
    form = AddForm
    template_name = 'add_pdf.html'

    def get_context_get(self, _, __):
        context = {'form': self.form, 'other': 1234}

        return context

    @staticmethod
    def obj_save(form: AddForm, request: HttpRequest, identifier: str = None):
        pdf = form.save(commit=False)
        pdf.owner = request.user.profile
        pdf.name = f'{pdf.name}_{identifier}'
        pdf.save()


class OverviewMixin(BaseMixin):
    @staticmethod
    def get_sorting_dict():
        """Get the sorting dict which describes the sorting in the overview page."""

        sorting_dict = {
            '': '-creation_date',
            'newest': '-creation_date',
            'oldest': 'creation_date',
            'title_asc': Lower('name'),
            'title_desc': Lower('name').desc(),
        }

        return sorting_dict

    @staticmethod
    def filter_objects(request: HttpRequest) -> QuerySet:
        """Filter the objects when performing a search in the overview."""

        pdfs = Pdf.objects.filter(owner=request.user.profile).all()
        pdfs = pdfs.exclude(name__icontains='fig')
        pdfs = pdfs.exclude(name__icontains='Kaki')

        return pdfs

    @staticmethod
    def get_extra_context(request: HttpRequest) -> dict:
        """get further information that needs to be passed to the template."""

        extra_context = {'other': 1234}

        return extra_context


class ObjectMixin(BaseMixin):
    @staticmethod
    def get_object(request: HttpRequest, pdf_id: str):
        """Get the pdf specified by the ID"""

        user_profile = request.user.profile
        pdf = user_profile.pdf_set.get(id=pdf_id)

        return pdf


class EditMixin(ObjectMixin):
    obj_class = Pdf
    fields_requiring_extra_processing = ['process_description']

    @staticmethod
    def get_edit_form_dict():
        form_dict = {'description': DescriptionForm, 'name': NameForm, 'process_description': DescriptionForm}

        return form_dict

    def get_edit_form_get(self, field_name: str, pdf: Pdf):
        form_dict = self.get_edit_form_dict()

        initial_dict = {
            'name': {'name': pdf.name},
            'description': {'description': pdf.description},
        }

        form = form_dict[field_name](initial=initial_dict[field_name])

        return form

    @staticmethod
    def process_field(field_name, pdf, request, form_data):
        if field_name == 'process_description':
            pdf.description = f'processed_{form_data['process_description']}'
            pdf.save()


class Add(BaseAddMixin, base_views.BaseAdd):
    """Add View"""


class Overview(OverviewMixin, base_views.BaseOverview):
    """Overview view"""


class OverviewQuery(BaseMixin, base_views.BaseOverviewQuery):
    """Overview query view"""


class Serve(ObjectMixin, base_views.BaseServe):
    """Serve view"""


class Download(ObjectMixin, base_views.BaseDownload):
    """Download view"""


class Details(ObjectMixin, base_views.BaseDetails):
    """Details View"""


class Edit(EditMixin, base_views.BaseDetailsEdit):
    """Edit View"""


class Delete(ObjectMixin, base_views.BaseDelete):
    """Delete View"""
