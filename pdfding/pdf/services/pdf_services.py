import json
import re
import traceback
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from logging import getLogger
from math import floor
from pathlib import Path
from shutil import copy
from uuid import uuid4

from core.settings import MEDIA_ROOT
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.db.models import QuerySet
from django.forms import ValidationError
from django.http import Http404, HttpRequest
from django.utils.translation import gettext_lazy as _
from pdf.models.collection_models import Collection
from pdf.models.pdf_models import (
    Metadata,
    Pdf,
    PdfAnnotation,
    PdfComment,
    PdfHighlight,
    delete_empty_dirs_after_rename_or_delete,
    get_file_path,
)
from pdf.models.tag_models import Tag
from pdf.models.workspace_models import Workspace
from pdf.services.tag_services import TagServices
from pdf.services.workspace_services import check_if_pdf_with_name_exists, get_pdfs_of_workspace
from pypdf import PdfReader
from pypdfium2 import PdfDocument
from users.models import PdfReadingInformation, Profile

logger = getLogger(__file__)


@dataclass
class TmpMetadata:
    abstract: str
    author: str
    keywords: str
    title: str


class PdfProcessingServices:
    @classmethod
    def create_pdf(
        cls,
        name: str,
        collection: Collection,
        pdf_file: File,
        description: str = '',
        notes: str = '',
        tag_string: str = '',
        file_directory: str = '',
        use_pdf_title: bool = False,
    ):
        tmp_metadata = cls.extract_metadata(pdf_file, collection.workspace)
        pdf_name, tmp_metadata = cls.create_pdf_name_and_title(
            name_from_form=name,
            use_pdf_title=use_pdf_title,
            tmp_metadata=tmp_metadata,
            pdf_file=pdf_file,
            workspace=collection.workspace,
        )

        pdf = Pdf.objects.create(
            name=pdf_name,
            description=description,
            notes=notes,
            file=pdf_file,
            file_directory=file_directory,
            collection=collection,
        )

        Metadata.objects.create(
            pdf=pdf,
            title=tmp_metadata.title,
            abstract=tmp_metadata.abstract,
            author=tmp_metadata.author,
            keywords=tmp_metadata.keywords,
        )

        # process with pdf libraries: add number of pages, thumbnail, preview, highlights and comments
        cls.process_with_pypdfium(pdf)
        cls.set_highlights_and_comments(pdf)

        # get unique tag names
        tag_names = Tag.parse_tag_string(tag_string)
        tags = TagServices.process_tag_names(tag_names, collection.workspace)

        pdf.tags.set(tags)
        workspace = pdf.collection.workspace
        for tag in tags:
            workspace.tag_set.add(tag)

        return pdf

    @classmethod
    def extract_metadata(cls, pdf_file: File, workspace: Workspace) -> TmpMetadata:
        """Extract the PDF's metadata."""

        try:
            pypdf_pdf = PdfReader(pdf_file)

            extracted_title = pypdf_pdf.metadata.get('/Title', '').strip()
            extracted_abstract = pypdf_pdf.metadata.get('/Subject', '').strip()
            extracted_author = pypdf_pdf.metadata.get('/Author', '').strip()
            extracted_keywords = pypdf_pdf.metadata.get('/Keywords', '').strip()

            tmp_metadata = TmpMetadata(
                title=extracted_title,
                abstract=extracted_abstract,
                author=extracted_author,
                keywords=extracted_keywords,
            )
        except Exception as e:  # nosec # noqa
            tmp_metadata = TmpMetadata('', '', '', '')
            logger.info(f'Could not extract medatata of "{pdf_file.name}" workspace "{workspace.id}" with Pypdf')
            logger.info(traceback.format_exc())

        return tmp_metadata

    @classmethod
    def create_pdf_name_and_title(
        cls, name_from_form: str, use_pdf_title: bool, tmp_metadata: TmpMetadata, pdf_file: File, workspace: Workspace
    ) -> tuple[str, TmpMetadata]:
        """Create the pdf name and its metadata title."""

        if use_pdf_title:
            if tmp_metadata.title:
                name = tmp_metadata.title
            else:
                name = create_name_from_file(pdf_file)
        else:
            name = name_from_form

        if not tmp_metadata.title:
            tmp_metadata.title = name

        if check_if_pdf_with_name_exists(name, workspace):
            name += f'_{str(uuid4())[:8]}'

        return name, tmp_metadata

    @classmethod
    def export_metadata_bibtex(cls, pdf: Pdf) -> BytesIO:
        """Export the the metadata to bibtex and write it to the buffer, so it can be used in a FileResponse."""

        name = pdf.metadata.title.replace(' ', '_')
        fields = [
            'abstract',
            'author',
            'doi',
            'journal',
            'keywords',
            'number',
            'pages',
            'publisher',
            'title',
            'url',
            'volume',
            'year',
        ]

        first_line = f'@{str(pdf.metadata.reference_type).lower()}{{{name},'
        bibtex_lines = [first_line]

        for field in fields:
            title = field.upper()
            value = getattr(pdf.metadata, field)

            if value:
                line = f'    {title} = {{{value}}},'
                bibtex_lines.append(line)

        bibtex_lines.append('}')

        bibtex_content = ('\n').join(bibtex_lines)
        buffer = BytesIO(bibtex_content.encode())

        return buffer

    @classmethod
    def import_metadata_bibtex(cls, bibtex_as_str: str, pdf: Pdf) -> None:
        """Import the metadata of a PDF from bibtex."""

        reference_type_matches = re.findall(r'\@(.*?)\{', bibtex_as_str)
        if len(reference_type_matches) != 1:
            raise ValidationError(_('Number of Bibtex entries needs to be one!'))

        reference_type = reference_type_matches[0]
        if reference_type.upper() not in Metadata.ReferenceType.names:
            raise ValidationError(_('Invalid reference type!'))
        else:
            pdf.metadata.reference_type = Metadata.ReferenceType[reference_type.upper()]

        kv = re.compile(r'\b(?P<key>\w+)\s*=\s*{(?P<value>[^}]+)}')
        field_dict = dict(kv.findall(bibtex_as_str))

        fields = [
            'ABSTRACT',
            'AUTHOR',
            'DOI',
            'JOURNAL',
            'KEYWORDS',
            'NUMBER',
            'PAGES',
            'PUBLISHER',
            'TITLE',
            'URL',
            'VOLUME',
            'YEAR',
        ]

        for field in fields:
            if field_dict.get(field):
                setattr(pdf.metadata, field.lower(), field_dict[field].strip())
            # do not set the title to empty
            elif field != 'TITLE':
                setattr(pdf.metadata, field.lower(), '')

        pdf.metadata.save()

    @classmethod
    def process_with_pypdfium(
        cls, pdf: Pdf, extract_thumbnail_and_preview: bool = True, delete_existing_thumbnail_and_preview: bool = False
    ):
        """
        Process the pdf with pypdfium. This will extract the number of pages and optionally the thumbnail + preview of
        the Pdf.
        """

        try:
            if delete_existing_thumbnail_and_preview:  # pragma: no cover
                pdf.thumbnail.delete()
                pdf.preview.delete()
                pdf.save()

            pdf_document = PdfDocument(pdf.file.path, autoclose=True)
            pdf.number_of_pages = len(pdf_document)
            if extract_thumbnail_and_preview:
                pdf = cls.set_thumbnail_and_preview(pdf, pdf_document)
            pdf_document.close()
            pdf.save()
        except Exception as e:  # nosec # noqa
            logger.info(f'Could not process "{pdf.name}" of workspace "{pdf.collection.workspace.id}" with Pypdfium')
            logger.info(traceback.format_exc())

    @staticmethod
    def set_thumbnail_and_preview(
        pdf: Pdf,
        pdf_document: PdfDocument,
        desired_thumbnail_width: int = 135,
        desired_thumbnail_width_height_ratio: float = 0.77,
        desired_preview_width: int = 450,
    ):
        """Extract and set the thumbnail and the preview image of the pdf file."""

        try:
            page = pdf_document[0]
            preview_width_height_ratio = page.get_width() / page.get_height()

            image_files = dict()
            for image_name, desired_width, desired_ratio in zip(
                ['thumbnail', 'preview'],
                [desired_thumbnail_width, desired_preview_width],
                [desired_thumbnail_width_height_ratio, preview_width_height_ratio],
            ):
                # extract image with predefined width
                scale_factor = desired_width / page.get_width()

                bitmap = page.render(scale=scale_factor)
                pil_image = bitmap.to_pil()

                desired_height = round(desired_width / desired_ratio)
                width, height = pil_image.size

                # we crop the image as we want a thumbnail with a ratio of 1.9 x 1. If the image is large enough we also
                # want the thumbnail not to start at the top but instead with a little offset
                height_diff = height - desired_height
                if image_name == 'thumbnail' and height_diff > 0:
                    offset = floor(0.15 * height_diff)
                    pil_image = pil_image.crop((0, offset, desired_width, desired_height + offset))

                # convert pillow image to django file
                image_io = BytesIO()
                pil_image.save(image_io, format='PNG')
                image_files[image_name] = image_io

            pdf.thumbnail = File(file=image_files['thumbnail'], name='thumbnail')
            pdf.preview = File(file=image_files['preview'], name='preview')

        except Exception as e:  # nosec # noqa
            logger.info(f'Could not extract thumbnail for "{pdf.name}" of workspace "{pdf.collection.workspace.id}"')
            logger.info(traceback.format_exc())

        return pdf

    @classmethod
    def set_highlights_and_comments(cls, pdf: Pdf, pdf_highlight_class=PdfHighlight, pdf_comment_class=PdfComment):
        """
        Set the highlights and comments of a pdf.

        We need to have pdf_highlight_class and pdf_comment_class arguments so that the migration using this function
        can overwrite the classes with the model 'blueprints' we get via
        apps.get_model(("pdf", "PdfHighlight/PdfComment")) results. Without this the migrations will not work.
        """

        try:
            # delete old comments and highlights
            pdf.pdfhighlight_set.all().delete()
            pdf.pdfcomment_set.all().delete()

            pypdf_pdf = PdfReader(pdf.file)
            pyreadium_pdf = PdfDocument(pdf.file, autoclose=True)

            for i, pypdf_page in enumerate(pypdf_pdf.pages):
                pdfium_page = pyreadium_pdf[i]

                if "/Annots" in pypdf_page:
                    try:
                        for annotation in pypdf_page["/Annots"]:
                            annotation_object = annotation.get_object()

                            annotation_type = annotation_object["/Subtype"]

                            if annotation_type in ["/FreeText", "/Highlight"]:
                                date_time_string = f'{annotation_object["/CreationDate"].split(':')[-1]}-+00:00'
                                creation_date = datetime.strptime(date_time_string, '%Y%m%d%H%M%S-%z')

                                if annotation_type == "/FreeText":
                                    comment_text = annotation_object["/Contents"]
                                    pdf_comment_class.objects.create(
                                        text=comment_text, page=i + 1, creation_date=creation_date, pdf=pdf
                                    )

                                elif annotation_type == "/Highlight":
                                    highlight_text = cls.extract_pdf_highlight_text(annotation_object, pdfium_page)
                                    pdf_highlight_class.objects.create(
                                        text=highlight_text, page=i + 1, creation_date=creation_date, pdf=pdf
                                    )
                    except Exception as e:  # nosec # noqa # pragma: no cover
                        workspace_id = pdf.collection.workspace.id

                        logger.info(
                            f'Could not extract highlights and comments for "{pdf.name}" of workspace "{workspace_id}"'
                        )
                        logger.info(traceback.format_exc())

            pyreadium_pdf.close()

        except Exception as e:  # nosec # noqa
            workspace_id = pdf.collection.workspace.id

            logger.info(f'Could not extract highlights and comments for "{pdf.name}" of workspace "{workspace_id}"')
            logger.info(traceback.format_exc())

    @staticmethod
    def extract_pdf_highlight_text(annotation, pdfium_page):
        """Extract the text from a highlight annotation"""

        # every highlighted lines is represented by a rectangle which consists of 4 quad points
        # the 4 quad points are stored in a list in the following way:
        # [bot_left_x, bot_left_y, bot_right_x, bot_right_y, top_left_x, top_left_y, top_right_x, top_right_y]

        quad_points = annotation["/QuadPoints"]
        rectangles = [quad_points[8 * i : 8 * (i + 1)] for i in range(len(quad_points) // 8)]  # noqa

        highlight_lines = []

        for rectangle in rectangles:
            text_page = pdfium_page.get_textpage()
            text = text_page.get_text_bounded(
                left=rectangle[0], bottom=rectangle[5], right=rectangle[2], top=rectangle[1]
            )

            # sometimes the same line is present multiple times, we only want one
            if not highlight_lines or text != highlight_lines[-1]:
                highlight_lines.append(text)

        highlight_text = ' '.join(highlight_lines).strip()
        highlight_text = re.sub(r'\s+', ' ', highlight_text)

        return highlight_text

    @classmethod
    def export_annotations(cls, profile: Profile, kind: str, pdf: Pdf = None) -> BytesIO:
        """Export annotations to json. Annotations can be comments or highlights of a single or all pdfs of a user."""

        if pdf:
            if kind == 'comments':
                pdf_annotations = pdf.pdfcomment_set.all()
            else:
                pdf_annotations = pdf.pdfhighlight_set.all()
        else:
            current_workspace_pdfs = get_pdfs_of_workspace(profile.current_workspace)
            if kind == 'comments':
                pdf_annotations = PdfComment.objects.filter(pdf__in=current_workspace_pdfs).all()
            else:
                pdf_annotations = PdfHighlight.objects.filter(pdf__in=current_workspace_pdfs).all()

        return cls.export_annotations_to_json_buffer(pdf_annotations, profile.current_workspace.id)

    @classmethod
    def export_annotations_to_json_buffer(cls, annotations: QuerySet[PdfAnnotation], workspace_id: str) -> BytesIO:
        """Export the provided annotations to json."""

        serialized_annotations = defaultdict(list)

        for annotation in annotations.order_by('page'):
            serialized_annotations[annotation.pdf.name].append(
                {
                    'text': annotation.text,
                    'page': annotation.page,
                    'creation_date': str(annotation.creation_date),
                }
            )

        serialized_annotations = dict(sorted(serialized_annotations.items(), key=lambda x: str.lower(x[0])))

        json_buffer = BytesIO()
        json_buffer.write(json.dumps(serialized_annotations, indent=2).encode())

        return json_buffer

    @classmethod
    def process_renaming_pdf(cls, pdf: Pdf):
        """
        Process the renaming of a pdf. This function saves the new name and updates its file name/path accordingly.
        """

        pdf_current_file_name = pdf.file.name
        current_path = MEDIA_ROOT / pdf.file.name
        pdf_new_file_name = get_file_path(pdf, None)

        new_path = MEDIA_ROOT / pdf_new_file_name

        if new_path != current_path:
            # make sure the parent dir exists
            new_path.parent.mkdir(parents=True, exist_ok=True)
            copy(current_path, new_path)
            pdf.file.name = pdf_new_file_name

        # The new name and file directory are already set to the pdf object by the form but not saved yet.
        pdf.save()

        if new_path != current_path:
            current_path.unlink(missing_ok=True)

            delete_empty_dirs_after_rename_or_delete(pdf_current_file_name, pdf.workspace.id, pdf.collection.name)


def check_object_access_allowed(get_object):
    """
    Return a Http404 exception when getting an object (e.g a pdf or shared pdf) that does not exist
    or access is not allowed.
    """

    def inner(request: HttpRequest, identifier: str):
        try:
            return get_object(request, identifier)
        except ValidationError:
            raise Http404("Given query not found...")
        except ObjectDoesNotExist:
            raise Http404("Given query not found...")

    return inner


def create_name_from_file(file: File | Path) -> str:
    """
    Get the file name from the file name. Will remove the '.pdf' from the file name.
    """

    name = file.name
    split_name = name.rsplit(sep='.', maxsplit=1)

    if len(split_name) > 1 and str.lower(split_name[-1]) == 'pdf':
        name = split_name[0]

    return name


def create_unique_name_from_file(file: File, workspace: Workspace) -> str:
    """
    Get the file name from the file name. Will remove the '.pdf' from the file name. If there is already
    a pdf with the same name then it will add a random 8 characters long suffix.
    """

    name = create_name_from_file(file)

    # if pdf name is already existing add a random 8 characters long string
    if check_if_pdf_with_name_exists(name, workspace):
        name += f'_{str(uuid4())[:8]}'

    return name


def get_pdf_info_list(workspace: Workspace) -> list[tuple]:
    """
    Get the pdf info list of a workspace. It contains information (name + file size) of each pdf of the profile. Each
    element is a tuple with (pdf name, pdf size).
    """

    pdf_info_list = []

    for pdf in get_pdfs_of_workspace(workspace):
        try:
            pdf_size = Path(pdf.file.path).stat().st_size
        except FileNotFoundError:  # pragma: no cover
            logger.info(f'File for PDF "{pdf.name}" of workspace "{pdf.collection.workspace.id}" not found!')
            pdf_size = 0

        pdf_info_list.append((pdf.name, pdf_size))

    return pdf_info_list


def get_or_create_pdf_reading_info(pdf: Pdf, profile: Profile) -> PdfReadingInformation:
    """Get the PdfReadingInformation. If it does not exist create it"""

    try:
        pdf_reading_info = PdfReadingInformation.objects.get(pdf=pdf, profile=profile)

    except ObjectDoesNotExist:
        pdf_reading_info = PdfReadingInformation.objects.create(
            pdf=pdf, profile=profile, current_page=1, last_viewed_date=datetime.now(tz=timezone.utc), views=0
        )

    return pdf_reading_info
