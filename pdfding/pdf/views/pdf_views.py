from datetime import datetime, timezone

from base import base_views
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.db.models import Q, QuerySet
from django.db.models.functions import Lower
from django.forms import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh
from pdf import forms, service
from pdf.models import Pdf, Tag
from pdf.service import PdfProcessingServices
from rapidfuzz import fuzz, utils
from users.models import Profile
from users.service import get_demo_pdf, get_viewer_colors


class BasePdfMixin:
    obj_name = 'pdf'


class AddPdfMixin(BasePdfMixin):
    def __init__(self):
        self.template_name = 'add_pdf.html'
        if settings.DEMO_MODE:  # pragma: no cover
            self.form = forms.AddFormNoFile
        else:
            self.form = forms.AddForm

    def get_context_get(self, _, __):
        """Get the context needed to be passed to the template containing the form for adding a PDF."""

        context = {'form': self.form}

        return context

    @staticmethod
    def obj_save(form: forms.AddForm | forms.AddFormNoFile, request: HttpRequest, __):
        """Save the PDF based on the submitted form."""

        name = form.data['name']
        description = form.data.get('description', '')
        notes = form.data.get('notes', '')
        tag_string = form.data.get('tag_string', '')
        profile = request.user.profile

        if settings.DEMO_MODE:
            pdf_file = get_demo_pdf()
        else:
            pdf_file = form.files['file']

        if form.data.get('use_file_name'):
            name = service.create_unique_name_from_file(pdf_file, request.user.profile)

        service.PdfProcessingServices.create_pdf(
            name=name,
            owner=profile,
            pdf_file=pdf_file,
            description=description,
            notes=notes,
            tag_string=tag_string,
        )


class BulkAddPdfMixin(BasePdfMixin):
    def __init__(self):
        self.template_name = 'bulk_add_pdf.html'
        if settings.DEMO_MODE:  # pragma: no cover
            self.form = forms.BulkAddFormNoFile
        else:
            self.form = forms.BulkAddForm

    def get_context_get(self, _, __):
        """Get the context needed to be passed to the template containing the form for bulk adding PDFs."""

        context = {'form': self.form}

        return context

    @staticmethod
    def obj_save(form: forms.BulkAddForm | forms.BulkAddFormNoFile, request: HttpRequest, __):
        """Save the multiple PDFs based on the submitted form."""

        profile = request.user.profile
        description = form.data.get('description', '')
        notes = form.data.get('notes', '')
        tag_string = form.data.get('tag_string', '')

        if form.data.get('skip_existing'):
            pdf_info_list = service.get_pdf_info_list(profile)
        else:
            pdf_info_list = []

        if settings.DEMO_MODE:
            files = [get_demo_pdf()]
        else:
            files = form.files.getlist('file')

        for file in files:
            # add file unless skipping existing is set and a PDF with the same name and file size already exists
            if not (
                form.data.get('skip_existing') and (service.create_name_from_file(file), file.size) in pdf_info_list
            ):
                pdf_name = service.create_unique_name_from_file(file, profile)

                service.PdfProcessingServices.create_pdf(
                    name=pdf_name,
                    owner=profile,
                    pdf_file=file,
                    description=description,
                    notes=notes,
                    tag_string=tag_string,
                )


class OverviewMixin(BasePdfMixin):
    overview_page_name = 'pdf_overview/overview_page'

    @staticmethod
    def get_sorting(request: HttpRequest):
        """Get the sorting of the overview page."""

        profile = request.user.profile

        sorting_dict = {
            'Newest': '-creation_date',
            'Oldest': 'creation_date',
            'Name_asc': Lower('name'),
            'Name_desc': Lower('name').desc(),
            'Least_viewed': 'views',
            'Most_viewed': '-views',
            'Recently_viewed': '-last_viewed_date',
        }

        return sorting_dict[profile.pdf_sorting]

    @classmethod
    def filter_objects(cls, request: HttpRequest) -> QuerySet:
        """Filter the PDFs when performing a search in the overview."""

        pdfs = request.user.profile.pdf_set

        search = request.GET.get('search', '')
        tags = request.GET.get('tags', [])

        # filter for starred or archived pdfs
        pdf_selection = request.GET.get('selection', '')

        if pdf_selection == 'archived':
            pdfs = pdfs.filter(archived=True)
        else:
            pdfs = pdfs.filter(archived=False)
            if pdf_selection == 'starred':
                pdfs = pdfs.filter(starred=True)

        if tags:
            tags = tags.split(' ')

        for tag in tags:
            pdfs = pdfs.filter(Q(tags__name=tag) | Q(tags__name__startswith=f'{tag}/')).distinct()

        if search:
            pdfs = cls.fuzzy_filter_pdfs(pdfs, search)

        return pdfs

    @staticmethod
    def fuzzy_filter_pdfs(pdfs: QuerySet, search: str) -> QuerySet:
        fuzzy_result = []

        for pdf in pdfs:
            w_ratio = fuzz.WRatio(search, pdf.name, processor=utils.default_process)
            partial_ratio = fuzz.partial_ratio(search, pdf.name, processor=utils.default_process)

            # better to be a bit more strict regarding this so we avoid false positives
            if (w_ratio + partial_ratio) / 2 > 85 or partial_ratio > 95:
                fuzzy_result.append(pdf.id)

        pdfs = pdfs.filter(id__in=fuzzy_result)

        return pdfs

    @staticmethod
    def get_extra_context(request: HttpRequest) -> dict:
        """get further information that needs to be passed to the template."""

        tag_query = request.GET.get('tags', [])
        if tag_query:
            tag_query = tag_query.split(' ')

        if request.GET.get('selection', '') in ['starred', 'archived']:
            special_pdf_selection = request.GET.get('selection')
            page = f'pdf_overview_{special_pdf_selection}'

        else:
            special_pdf_selection = ''
            page = 'pdf_overview'

        extra_context = {
            'search_query': request.GET.get('search', ''),
            'tag_query': tag_query,
            'special_pdf_selection': special_pdf_selection,
            'tag_info_dict': service.TagServices.get_tag_info_dict(request.user.profile),
            'page': page,
            'layout': request.user.profile.layout,
        }

        return extra_context


class PdfMixin(BasePdfMixin):
    @staticmethod
    @service.check_object_access_allowed
    def get_object(request: HttpRequest, pdf_id: str):
        """Get the pdf specified by the ID"""

        user_profile = request.user.profile
        pdf = user_profile.pdf_set.get(id=pdf_id)

        return pdf


class TagMixin:
    @staticmethod
    @service.check_object_access_allowed
    def get_tag_by_name(request: HttpRequest, identifier: str):
        """Get the tag specified by the name"""

        user_profile = request.user.profile
        tag = user_profile.tag_set.filter(name__iexact=identifier).first()

        return tag

    @staticmethod
    @service.check_object_access_allowed
    def get_tags_by_name(request: HttpRequest, identifier: str):
        """Get the pdf specified by the name and its children"""

        user_profile = request.user.profile

        tag_exact = user_profile.tag_set.filter(name__iexact=identifier).first()

        if tag_exact:
            tags = [tag_exact]
        else:
            tags = []

        tags.extend(user_profile.tag_set.filter(name__istartswith=f'{identifier}/'))

        return tags


class EditPdfMixin(PdfMixin):
    obj_class = Pdf
    fields_requiring_extra_processing = ['tags']

    @staticmethod
    def get_edit_form_dict():
        """Get the forms of the fields that can be edited as a dict."""

        form_dict = {
            'description': forms.DescriptionForm,
            'name': forms.NameForm,
            'tags': forms.PdfTagsForm,
            'notes': forms.NotesForm,
        }

        return form_dict

    def get_edit_form_get(self, field_name: str, pdf: Pdf):
        """Get the form belonging to the specified field."""

        form_dict = self.get_edit_form_dict()

        initial_dict = {
            'name': {'name': pdf.name},
            'description': {'description': pdf.description},
            'notes': {'notes': pdf.notes},
            'tags': {'tag_string': ' '.join(sorted([tag.name for tag in pdf.tags.all()]))},
        }

        form = form_dict[field_name](initial=initial_dict[field_name])

        return form

    @staticmethod
    def process_field(field_name, pdf, request, form_data):
        """Process fields that are not covered in the base edit view."""

        if field_name == 'tags':
            tag_string = form_data['tag_string']
            tag_names = Tag.parse_tag_string(tag_string)

            # check if tag needs to be deleted
            for tag in pdf.tags.all():
                if tag.name not in tag_names and tag.pdf_set.count() == 1:
                    tag.delete()

            tags = service.TagServices.process_tag_names(tag_names, request.user.profile)

            pdf.tags.set(tags)


@login_not_required
def redirect_to_overview(request: HttpRequest):  # pragma: no cover
    """
    Simple view for redirecting to the pdf overview. This is used when the root url is accessed.

    GET: Redirect to the PDF overview page.
    """

    return redirect('pdf_overview')


class ViewerView(PdfMixin, View):
    """The view responsible for displaying the PDF file specified by the PDF id in the browser."""

    def get(self, request: HttpRequest, identifier: str):
        """Display the PDF file in the browser"""

        # increase view counter by 1
        pdf = self.get_object(request, identifier)
        pdf.views += 1
        pdf.last_viewed_date = datetime.now(timezone.utc)
        pdf.save()

        color_dict = get_viewer_colors(request.user.profile)

        return render(
            request,
            'viewer.html',
            {
                'current_page': pdf.current_page,
                'pdf_id': identifier,
                'revision': pdf.revision,
                'tab_title': pdf.name,
                'theme_color': color_dict['theme_color'],
                'primary_color': color_dict['primary_color'],
                'secondary_color': color_dict['secondary_color'],
                'text_color': color_dict['text_color'],
                'user_view_bool': True,
            },
        )


class GetNotes(PdfMixin, View):
    """View for getting a pdf's markdown notes as html, so it can be displayed via htmx."""

    def get(self, request: HttpRequest, identifier: str):
        """Get a pdf's markdown notes as html"""

        if request.htmx:
            pdf = self.get_object(request, identifier)

            return render(request, 'partials/notes.html', {'pdf_notes': pdf.notes_html})

        return redirect('pdf_overview')


class UpdatePage(PdfMixin, View):
    """
    View for updating the current page of the viewed PDF. This is triggered everytime the page the user changes the
    displayed page in the browser.
    """

    def post(self, request: HttpRequest):
        """Change the current page."""

        pdf_id = request.POST.get('pdf_id')
        pdf = self.get_object(request, pdf_id)

        # update current page
        current_page = request.POST.get('current_page')
        pdf.current_page = current_page
        pdf.save()

        return HttpResponse(status=200)


class UpdatePdf(PdfMixin, View):
    """
    View for updating the PDF file. This is triggered everytime the user saves a modified PDF.
    """

    def post(self, request: HttpRequest):
        """Change the current page."""

        pdf_id = request.POST.get('pdf_id')
        pdf = self.get_object(request, pdf_id)

        if settings.DEMO_MODE:
            updated_pdf = get_demo_pdf()
        else:
            updated_pdf = request.FILES.get('updated_pdf')
        try:
            # make sure a valid pdf is sent
            updated_pdf = forms.CleanHelpers.clean_file(updated_pdf)
            pdf.file = updated_pdf
            pdf.revision += 1
            pdf.save()

            PdfProcessingServices.set_highlights_and_comments(pdf)

            return HttpResponse(status=200)
        except ValidationError:
            return HttpResponse(status=422)


class Overview(OverviewMixin, base_views.BaseOverview):
    """
    View for the PDF overview page. This view performs the searching and sorting of the PDFs. It's also responsible for
    paginating the PDFs.
    """


class OverviewQuery(BasePdfMixin, base_views.BaseOverviewQuery):
    """View for performing searches and sorting on the PDF overview page."""


class Serve(PdfMixin, base_views.BaseServe):
    """View used for serving PDF files specified by the PDF id"""


class Add(AddPdfMixin, base_views.BaseAdd):
    """View for adding new PDF files."""


class BulkAdd(BulkAddPdfMixin, base_views.BaseAdd):
    """View for bulk adding new PDF files."""


class Details(PdfMixin, base_views.BaseDetails):
    """View for displaying the details page of a PDF."""


class Edit(EditPdfMixin, base_views.BaseDetailsEdit):
    """
    The view for editing a PDF's name, tags and description. The field, that is to be changed, is specified by the
    'field' argument.
    """


class Delete(PdfMixin, base_views.BaseDelete):
    """View for deleting the PDF specified by its ID."""

    def get(self, request: HttpRequest, identifier: str):
        """Triggered by htmx. Display an inline form for deleting the pdf."""

        if request.htmx:
            pdf = self.get_object(request, identifier)

            return render(
                request,
                'partials/delete_pdf.html',
                {'pdf_id': identifier, 'pdf_name': pdf.name},
            )

        return redirect('pdf_overview')


class Download(PdfMixin, base_views.BaseDownload):
    """View for downloading the PDF specified by the ID."""


class ServeThumbnail(PdfMixin, base_views.BaseServe):
    """View used for serving the thumbnail specified by the PDF id"""

    @staticmethod
    def get_file_path(pdf):  # pragma: no cover
        return pdf.thumbnail.name


class ServePreview(PdfMixin, base_views.BaseServe):
    """View used for serving the preview specified by the PDF id"""

    @staticmethod
    def get_file_path(pdf):  # pragma: no cover
        return pdf.preview.name


class ShowPreview(PdfMixin, View):
    """The view for showing the preview of a PDF in the overview."""

    def get(self, request: HttpRequest, identifier: str):
        """Get a pdf's preview as html"""

        if request.htmx:
            pdf = self.get_object(request, identifier)

            if pdf.preview:
                preview_available = True
            else:
                preview_available = False
            return render(request, 'partials/preview.html', {'pdf_id': pdf.id, 'preview_available': preview_available})

        return redirect('pdf_overview')


class EditTag(TagMixin, View):
    """
    The view for editing the name of a tag in the overview.
    """

    def get(self, request: HttpRequest):
        """Triggered by htmx. Display an inline form for editing the tag name."""

        if request.htmx:
            tag_name = request.GET.get('tag_name', '')

            return render(
                request,
                'partials/tag_name_form.html',
                {'tag_name': tag_name, 'form': forms.TagNameForm(initial={'name': tag_name})},
            )

        return redirect('pdf_overview')

    def post(self, request: HttpRequest):
        """
        POST: Change the Tag name.
        """

        redirect_url = request.META.get('HTTP_REFERER', 'pdf_overview')
        user_profile = request.user.profile
        original_tag_name = request.POST.get('current_name', '')
        form = forms.TagNameForm(request.POST)

        if form.is_valid():
            new_name = form.data.get('name')

            if user_profile.tag_tree_mode:
                tags = self.get_tags_by_name(request, original_tag_name)

                for tag in tags:
                    # change
                    new_tag_name = new_name
                    if tag.name != new_name:
                        new_tag_name = tag.name.replace(original_tag_name, new_tag_name)

                    self.rename_tag(tag, new_tag_name, user_profile)
            else:
                tag = self.get_tag_by_name(request, original_tag_name)
                self.rename_tag(tag, new_name, user_profile)

            redirect_url = service.adjust_referer_for_tag_view(redirect_url, original_tag_name, new_name)
        else:
            try:
                messages.warning(request, dict(form.errors)['name'][0])
            except:  # noqa # pragma: no cover
                messages.warning(request, 'Input is not valid!')

        return redirect(redirect_url)

    @staticmethod
    def rename_tag(tag: Tag, new_tag_name: str, profile: Profile):
        """
        Rename a tag. If tag name already exist merge.
        """

        existing_tag = profile.tag_set.filter(name__iexact=new_tag_name).first()

        # if there is already a tag with the same name, delete the tag and add the existing tag to the pdfs
        if existing_tag and str(existing_tag.id) != tag.id:
            pdfs = profile.pdf_set
            pdfs_with_tag = pdfs.filter(tags__id=tag.id)

            for pdf_with_tag in pdfs_with_tag:
                # we are safe to use add, even if the pdf already has the tag as the documentation states:
                # Using add() on a relation that already exists won’t duplicate the relation,
                # but it will still trigger signals.
                pdf_with_tag.tags.add(existing_tag)
            tag.delete()
        else:
            tag.name = new_tag_name
            tag.save()


class DeleteTag(TagMixin, View):
    """View for deleting the tag specified by its ID."""

    def post(self, request: HttpRequest):
        """Delete the specified tag."""

        redirect_url = request.META.get('HTTP_REFERER', 'pdf_overview')

        if request.htmx:
            tag_name = request.POST.get('tag_name', '')

            if request.user.profile.tag_tree_mode:
                tags = self.get_tags_by_name(request, tag_name)
            else:
                tags = [self.get_tag_by_name(request, tag_name)]

            for tag in tags:
                tag.delete()

            redirect_url = service.adjust_referer_for_tag_view(redirect_url, tag_name, '')

            return HttpResponseClientRedirect(redirect_url)

        return redirect(redirect_url)


class Star(PdfMixin, View):
    """View for starring and unstarring pdfs."""

    def post(self, request: HttpRequest, identifier: str):
        """Star or unstar the specified pdf."""

        if request.htmx:
            pdf = self.get_object(request, identifier)
            pdf.starred = not pdf.starred

            # starred pdfs will be unarchived
            if pdf.archived:
                pdf.archived = False

            pdf.save()

            return HttpResponseClientRefresh()

        return redirect('pdf_overview')


class Archive(PdfMixin, View):
    """View for archiving and unarchiving pdfs."""

    def post(self, request: HttpRequest, identifier: str):
        """Archive or unarchive the specified pdf."""

        if request.htmx:
            pdf = self.get_object(request, identifier)
            pdf.archived = not pdf.archived

            # archived pdfs cannot be starred
            if pdf.starred:
                pdf.starred = False

            pdf.save()

            return HttpResponseClientRefresh()

        return redirect('pdf_overview')
