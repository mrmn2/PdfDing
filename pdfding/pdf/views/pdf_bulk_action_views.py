from django.contrib import messages
from django.http import Http404, HttpRequest
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from pdf.models.pdf_models import Pdf
from pdf.models.tag_models import Tag
from pdf.models.workspace_models import Workspace
from pdf.services.collection_services import change_collection_of_pdf
from pdf.services.tag_services import TagServices
from pdf.services.workspace_services import check_if_collection_part_of_workspace
from pdf.views.pdf_views import PdfMixin


class BulkActions(PdfMixin, View):
    def post(self, request: HttpRequest):
        bulk_action = request.POST.get('selected_bulk_action')
        selected_pdf_ids = request.POST.get('bulk_selected_pdfs', '').strip()

        if selected_pdf_ids:
            selected_pdf_ids = selected_pdf_ids.split(',')
        else:
            selected_pdf_ids = []

        pdfs = [self.get_object(request, pdf_id) for pdf_id in selected_pdf_ids]

        if pdfs:
            match bulk_action:
                case 'archive':
                    self.archive(pdfs)
                case 'delete':
                    confirmation = request.POST.get('delete_confirmation')
                    self.delete(pdfs, confirmation)
                case 'set_collection':
                    collection_id = request.POST.get('collection_id')
                    self.set_collection(pdfs, request.user.profile.current_workspace, collection_id)
                case 'set_tags':
                    tag_string = request.POST.get('tag_string')
                    self.set_tags(pdfs, tag_string, request)
                case 'star':
                    self.star(pdfs)

        return redirect(request.META.get('HTTP_REFERER', 'pdf_overview'))

    @staticmethod
    def archive(pdfs: list[Pdf]) -> None:
        """Archive of PDFs."""

        for pdf in pdfs:
            pdf.archived = True
            pdf.save()

    @staticmethod
    def delete(pdfs: list[Pdf], delete_confirmation: str) -> None:
        """Delete of PDFs."""

        if delete_confirmation == 'yes':
            for pdf in pdfs:
                pdf.delete()

    @staticmethod
    def set_collection(pdfs: list[Pdf], current_workspace: Workspace, collection_id: str) -> None:
        """Set the collection of the Pdfs."""

        if check_if_collection_part_of_workspace(current_workspace, collection_id):
            for pdf in pdfs:
                change_collection_of_pdf(pdf, collection_id)
        else:
            raise Http404('Collection does not exists in the current workspace!')

    @staticmethod
    def set_tags(pdfs: list[Pdf], tag_string: str, request: HttpRequest) -> None:
        """Set the tags of the Pdfs."""

        for char in tag_string:
            if not (char.isalnum() or char in ['/', '-', '_', ' ']):
                messages.warning(request, _('Only letters, numbers, "/", "-" and "_" are valid characters!'))

        tag_names = Tag.parse_tag_string(tag_string)
        tags = TagServices.process_tag_names(tag_names, pdfs[0].collection.workspace)

        for pdf in pdfs:
            # check if tag needs to be deleted
            for tag in pdf.tags.all():
                if tag.name not in tag_names and tag.pdf_set.count() == 1:
                    tag.delete()

            pdf.tags.set(tags)

    @staticmethod
    def star(pdfs: list[Pdf]) -> None:
        """Star the PDFs."""

        for pdf in pdfs:
            pdf.starred = True
            pdf.save()
