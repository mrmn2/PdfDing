from datetime import datetime, timezone

from base import base_views
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.db.models import Q, QuerySet
from django.db.models.functions import Lower
from django.forms import ValidationError
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh
from pdf import forms
from pdf.models.collection_models import Collection
from pdf.models.pdf_models import Pdf, PdfComment, PdfHighlight
from pdf.models.tag_models import Tag
from pdf.services import pdf_services
from pdf.services.pdf_services import PdfProcessingServices
from pdf.services.tag_services import TagServices
from pdf.services.workspace_services import get_pdfs_of_workspace
from rapidfuzz import fuzz, utils
from users.models import Profile
from users.service import get_demo_pdf, get_viewer_theme_and_color


class BasePdfMixin:
    obj_name = 'pdf'


class AddPdfMixin(BasePdfMixin):
    def __init__(self):
        self.template_name = 'add_pdf.html'
        if settings.DEMO_MODE:  # pragma: no cover
            self.form = forms.AddFormNoFile
        else:
            self.form = forms.AddForm

    def get_context_get(self, request: HttpRequest, _):
        """Get the context needed to be passed to the template containing the form for adding a PDF."""

        context = {'form': self.form(profile=request.user.profile)}

        return context

    @staticmethod
    def obj_save(form: forms.AddForm | forms.AddFormNoFile, request: HttpRequest, __):
        """Save the PDF based on the submitted form."""

        name = form.cleaned_data['name']
        description = form.cleaned_data.get('description', '')
        notes = form.cleaned_data.get('notes', '')
        tag_string = form.cleaned_data.get('tag_string', '')
        file_directory = form.cleaned_data.get('file_directory', '')
        collection_id = form.cleaned_data.get('collection')
        collection = Collection.objects.get(id=collection_id)
        if settings.DEMO_MODE:
            pdf_file = get_demo_pdf()
        else:
            pdf_file = form.cleaned_data['file']

        if form.data.get('use_file_name'):
            name = pdf_services.create_unique_name_from_file(pdf_file, collection.workspace)

        PdfProcessingServices.create_pdf(
            name=name,
            collection=collection,
            pdf_file=pdf_file,
            description=description,
            notes=notes,
            tag_string=tag_string,
            file_directory=file_directory,
        )


class BulkAddPdfMixin(BasePdfMixin):
    def __init__(self):
        self.template_name = 'bulk_add_pdf.html'
        if settings.DEMO_MODE:  # pragma: no cover
            self.form = forms.BulkAddFormNoFile
        else:
            self.form = forms.BulkAddForm

    def get_context_get(self, request: HttpRequest, _):
        """Get the context needed to be passed to the template containing the form for bulk adding PDFs."""

        context = {'form': self.form}
        context = {'form': self.form(profile=request.user.profile)}

        return context

    @staticmethod
    def obj_save(form: forms.BulkAddForm | forms.BulkAddFormNoFile, request: HttpRequest, __):
        """Save the multiple PDFs based on the submitted form."""

        description = form.data.get('description', '')
        notes = form.data.get('notes', '')
        tag_string = form.data.get('tag_string', '')
        file_directory = form.data.get('file_directory', '')
        collection_id = form.data.get('collection')
        collection = Collection.objects.get(id=collection_id)
        workspace = collection.workspace

        if form.data.get('skip_existing'):
            pdf_info_list = pdf_services.get_pdf_info_list(workspace)
        else:
            pdf_info_list = []

        if settings.DEMO_MODE:
            files = [get_demo_pdf()]
        else:
            files = form.files.getlist('file')

        for file in files:
            # add file unless skipping existing is set and a PDF with the same name and file size already exists
            if not (
                form.data.get('skip_existing')
                and (pdf_services.create_name_from_file(file), file.size) in pdf_info_list
            ):
                pdf_name = pdf_services.create_unique_name_from_file(file, workspace)

                PdfProcessingServices.create_pdf(
                    name=pdf_name,
                    collection=collection,
                    pdf_file=file,
                    description=description,
                    notes=notes,
                    file_directory=file_directory,
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

        pdfs = request.user.profile.current_pdfs

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
            'layout': request.user.profile.layout,
            'needs_nagging': request.user.profile.needs_nagging,
            'page': page,
            'search_query': request.GET.get('search', ''),
            'special_pdf_selection': special_pdf_selection,
            'tag_info_dict': TagServices.get_tag_info_dict(request.user.profile),
            'tag_query': tag_query,
        }

        return extra_context


class PdfMixin(BasePdfMixin):
    @staticmethod
    @pdf_services.check_object_access_allowed
    def get_object(request: HttpRequest, pdf_id: str):
        """Get the pdf specified by the ID"""

        user_profile = request.user.profile
        pdf = user_profile.all_pdfs.get(id=pdf_id)

        return pdf


class TagMixin:
    @staticmethod
    @pdf_services.check_object_access_allowed
    def get_tag_by_name(request: HttpRequest, identifier: str):
        """Get the tag specified by the name"""

        user_profile = request.user.profile
        tag = user_profile.tags.filter(name__iexact=identifier).first()

        return tag

    @staticmethod
    @pdf_services.check_object_access_allowed
    def get_tags_by_name(request: HttpRequest, identifier: str):
        """Get the pdf specified by the name and its children"""

        user_profile = request.user.profile

        tag_exact = user_profile.tags.filter(name__iexact=identifier).first()

        if tag_exact:
            tags = [tag_exact]
        else:
            tags = []

        tags.extend(user_profile.tags.filter(name__istartswith=f'{identifier}/'))

        return tags


class EditPdfMixin(PdfMixin):
    obj_class = Pdf
    fields_requiring_extra_processing = ['file_directory', 'name', 'tags']

    @staticmethod
    def get_edit_form_dict():
        """Get the forms of the fields that can be edited as a dict."""

        form_dict = {
            'description': forms.DescriptionForm,
            'name': forms.NameForm,
            'tags': forms.PdfTagsForm,
            'notes': forms.NotesForm,
            'file_directory': forms.FileDirectoryForm,
        }

        return form_dict

    def get_edit_form_get(self, field_name: str, pdf: Pdf):
        """Get the form belonging to the specified field."""

        form_dict = self.get_edit_form_dict()

        initial_dict = {
            'name': {'name': pdf.name},
            'description': {'description': pdf.description},
            'notes': {'notes': pdf.notes},
            'file_directory': {'file_directory': pdf.file_directory},
            'tags': {'tag_string': ' '.join(sorted([tag.name for tag in pdf.tags.all()]))},
        }

        form = form_dict[field_name](initial=initial_dict[field_name])

        return form

    @classmethod
    def process_field(cls, field_name: str, pdf: Pdf, request: HttpRequest, form_data: dict):
        """Process fields that are not covered in the base edit view."""

        if field_name == 'tags':
            tag_string = form_data.get('tag_string', '')
            tag_names = Tag.parse_tag_string(tag_string)

            # check if tag needs to be deleted
            for tag in pdf.tags.all():
                if tag.name not in tag_names and tag.pdf_set.count() == 1:
                    tag.delete()

            tags = TagServices.process_tag_names(tag_names, pdf.collection.workspace)

            pdf.tags.set(tags)

        elif field_name == 'name':
            existing_obj = (
                get_pdfs_of_workspace(pdf.workspace).filter(name__iexact=form_data.get('name').strip()).first()
            )

            if existing_obj and str(existing_obj.id) != str(pdf.id):
                messages.warning(request, 'This name is already used by another PDF!')
            else:
                PdfProcessingServices.process_renaming_pdf(pdf)

        elif field_name == 'file_directory':
            PdfProcessingServices.process_renaming_pdf(pdf)


class AnnotationOverviewMixin:
    obj_name = 'pdf_annotation'
    overview_page_name = 'pdf_annotation_overview/overview_page'

    @staticmethod
    def get_sorting(request: HttpRequest):  # pragma: no cover
        """Get the sorting of the overview page."""

        profile = request.user.profile

        sorting_dict = {
            'Newest': '-creation_date',
            'Oldest': 'creation_date',
        }

        return sorting_dict[profile.annotation_sorting]


class HighlightOverviewMixin(AnnotationOverviewMixin):
    @staticmethod
    def filter_objects(request: HttpRequest) -> QuerySet:
        """
        Filter the PDF highlights in the overview. As there is no filtering needed this is just a dummy function.
        """

        pdfs = request.user.profile.current_pdfs
        highlights = PdfHighlight.objects.filter(pdf__in=pdfs)

        return highlights

    @staticmethod
    def get_extra_context(_) -> dict:  # pragma: no cover
        """get further information that needs to be passed to the template."""

        return {
            'page': 'pdf_highlight_overview',
            'get_next_overview_page': 'get_next_pdf_highlight_overview_page',
            'kind': 'highlights',
        }


class CommentOverviewMixin(AnnotationOverviewMixin):
    @staticmethod
    def filter_objects(request: HttpRequest) -> QuerySet:
        """
        Filter the PDF comments in the overview. As there is no filtering needed this is just a dummy function.
        """

        pdfs = request.user.profile.current_pdfs
        comments = PdfComment.objects.filter(pdf__in=pdfs)

        return comments

    @staticmethod
    def get_extra_context(_) -> dict:  # pragma: no cover
        """get further information that needs to be passed to the template."""

        return {
            'page': 'pdf_comment_overview',
            'get_next_overview_page': 'get_next_pdf_comment_overview_page',
            'kind': 'comments',
        }


class DetailsAnnotationOverviewMixin(AnnotationOverviewMixin):
    obj_name = 'pdf_details_annotation'


class DetailsHighlightOverviewMixin(DetailsAnnotationOverviewMixin, PdfMixin):
    @classmethod
    def filter_objects(cls, request: HttpRequest, identifier: str) -> QuerySet:
        """
        Filter the highlights of a single pdf.
        """

        pdf = cls.get_object(request, identifier)

        highlights = pdf.pdfhighlight_set.all()

        return highlights

    @classmethod
    def get_extra_context(cls, request: HttpRequest, identifier) -> dict:  # pragma: no cover
        """get further information that needs to be passed to the template."""

        pdf = cls.get_object(request, identifier)

        return {
            'page': 'pdf_details_highlights',
            'get_next_overview_page': 'get_next_pdf_details_highlight_overview_page',
            'pdf': pdf,
            'kind': 'highlights',
        }


class DetailsCommentOverviewMixin(DetailsAnnotationOverviewMixin, PdfMixin):
    @classmethod
    def filter_objects(cls, request: HttpRequest, identifier: str) -> QuerySet:
        """
        Filter the comments of a single pdf.
        """

        pdf = cls.get_object(request, identifier)

        comments = pdf.pdfcomment_set.all()

        return comments

    @classmethod
    def get_extra_context(cls, request: HttpRequest, identifier) -> dict:  # pragma: no cover
        """get further information that needs to be passed to the template."""

        pdf = cls.get_object(request, identifier)

        return {
            'page': 'pdf_details_comments',
            'get_next_overview_page': 'get_next_pdf_details_comment_overview_page',
            'pdf': pdf,
            'kind': 'comments',
        }


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

        theme, theme_color = get_viewer_theme_and_color(request.user.profile)

        page = request.GET.get('page')

        if page:
            current_page = page
        else:
            current_page = pdf.current_page

        return render(
            request,
            'viewer.html',
            {
                'current_page': current_page,
                'pdf_id': identifier,
                'revision': pdf.revision,
                'tab_title': pdf.name,
                'theme': theme,
                'theme_color': theme_color,
                'user_view_bool': True,
                'keep_screen_awake': request.user.profile.pdf_keep_screen_awake,
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

    def do_extra_action(self, request: HttpRequest):
        """When nagging modal is shown, set last time nagged to current datetime"""

        profile = request.user.profile

        if profile.needs_nagging:
            profile.last_time_nagged = datetime.now(tz=timezone.utc)
            profile.save()


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


class HighlightOverview(HighlightOverviewMixin, base_views.BaseOverview):
    """
    View for the PDF highlight overview page. This view performs sorting of the PDFs highlights. It's also responsible
    for paginating the PDF highlights.
    """


class CommentOverview(CommentOverviewMixin, base_views.BaseOverview):
    """
    View for the PDF comment overview page. This view performs sorting of the PDFs comments. It's also responsible
    for paginating the PDF comments.
    """


class DetailsHighlightOverview(DetailsHighlightOverviewMixin, base_views.BaseOverview):
    """
    View for the highlights of a single pdf. This view performs sorting of the PDFs highlights. It's also responsible
    for paginating the PDF highlights.
    """


class DetailsCommentOverview(DetailsCommentOverviewMixin, base_views.BaseOverview):
    """
    View for the comments of a single pdf. This view performs sorting of the PDFs comments. It's also responsible
    for paginating the PDF comments.
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

            redirect_url = TagServices.adjust_referer_for_tag_view(redirect_url, original_tag_name, new_name)
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

        existing_tag = profile.tags.filter(name__iexact=new_tag_name).first()

        # if there is already a tag with the same name, delete the tag and add the existing tag to the pdfs
        if existing_tag and str(existing_tag.id) != tag.id:
            pdfs = get_pdfs_of_workspace(profile.current_workspace)
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

            redirect_url = TagServices.adjust_referer_for_tag_view(redirect_url, tag_name, '')

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


class ExportAnnotations(View, PdfMixin):
    """View for exporting annotations to yaml and downloading the file."""

    def get(self, request: HttpRequest, kind: str, identifier: str = ''):
        """Return the exported annotations yaml as a FileResponse."""

        if kind not in ['comments', 'highlights']:  # pragma: no cover
            return redirect('pdf_overview')
        else:
            profile = request.user.profile

            if identifier:
                pdf = PdfMixin.get_object(request, identifier)
                PdfProcessingServices.export_annotations(profile, kind, pdf)
            else:
                PdfProcessingServices.export_annotations(profile, kind)

            export_path = PdfProcessingServices.get_annotation_export_path(str(profile.user.id))
            response = FileResponse(open(export_path, 'rb'), as_attachment=True, filename='export.yaml')

            # delete the file
            export_path.unlink()

            return response
