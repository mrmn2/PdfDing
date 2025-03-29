import re
import traceback
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta, timezone
from io import BytesIO
from logging import getLogger
from math import floor
from pathlib import Path
from shutil import copy
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from core.settings import MEDIA_ROOT
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.db.models import QuerySet
from django.db.models.functions import Lower
from django.forms import ValidationError
from django.http import Http404, HttpRequest
from django.urls import reverse
from pdf.models import (
    Pdf,
    PdfAnnotation,
    PdfComment,
    PdfHighlight,
    Tag,
    delete_empty_dirs_after_rename_or_delete,
    get_file_path,
)
from pypdf import PdfReader
from pypdfium2 import PdfDocument
from ruamel.yaml import YAML
from users.models import Profile

logger = getLogger(__file__)


class TagServices:
    @staticmethod
    def process_tag_names(tag_names: list[str], owner_profile: Profile) -> list[Tag]:
        """
        Process the specified tags. If the tag is existing it will simply be added to the return list. If it does not
        exist it, it will be created and then be added to the return list.
        """

        tags = []
        for tag_name in tag_names:
            try:
                tag = Tag.objects.get(owner=owner_profile, name=tag_name)
            except Tag.DoesNotExist:
                tag = Tag.objects.create(name=tag_name, owner=owner_profile)

            tags.append(tag)

        return tags

    @classmethod
    def get_tag_info_dict(cls, profile: Profile) -> dict[str, dict]:
        """
        Get the tag info dict used for displaying the tags in the pdf overview.
        """

        if profile.tag_tree_mode:
            tag_info_dict = cls.get_tag_info_dict_tree_mode(profile)
        else:
            tag_info_dict = cls.get_tag_info_dict_normal_mode(profile)

        return tag_info_dict

    @staticmethod
    def get_tag_info_dict_normal_mode(profile: Profile) -> dict[str, dict]:
        """
        Get the tag info dict used for displaying the tags in the pdf overview when normal mode is activated.
        Key: name of the tag. Value: display name of the tag
        """

        # it is important that the tags are sorted. As parent tags need come before children,
        # e.g. "programming" before "programming/python"
        tags = profile.tag_set.all().order_by(Lower('name'))
        tag_info_dict = OrderedDict()

        for tag in tags:
            tag_info_dict[tag.name] = {'display_name': tag.name}

        return tag_info_dict

    @staticmethod
    def get_tag_info_dict_tree_mode(profile: Profile) -> dict[str, dict]:
        """
        Get the tag info dict used for displaying the tags in the pdf overview when tree mode is activated.
        Key: name of the tag. Value: Information about the tag necessary for displaying it in tree mode, e.g. display
        name, indent level, has_children, slug and the condition for showing it via alpine js.
        """

        # it is important that the tags are sorted. As parent tags need come before children,
        # e.g. "programming" before "programming/python"
        tags = profile.tag_set.all().order_by(Lower('name'))
        tag_info_dict = OrderedDict()

        for tag in tags:
            tag_split = tag.name.split('/', maxsplit=2)
            current = ''
            words = []
            show_conditions = []

            for level, word in enumerate(tag_split):
                prev = current
                words.append(word)
                current = '/'.join(words)

                if level:
                    tag_info_dict[prev]['has_children'] = True

                if current not in tag_info_dict:
                    tag_info_dict[current] = {
                        'display_name': current.split('/', level)[-1],
                        'level': level,
                        'has_children': False,
                        'show_cond': ' && '.join(show_conditions),
                        'slug': current.replace('-', '_').replace('/', '___'),
                    }

                # alpine js will not work if the tag starts with a number. therefore, we have "tag_" in front so it
                # will still work.
                show_conditions.append(f'tag_{current.replace('-', '_').replace('/', '___')}_show_children')

        return tag_info_dict

    def adjust_referer_for_tag_view(referer_url: str, replace: str, replace_with: str) -> str:
        """
        Adjust the referer url for tag views. If a tag is renamed or deleted, the query part of the tag string will be
        adjusted accordingly. E.g. for renaming tag 'some' to 'other': 'http://127.0.0.1:5000/pdf/?q=%23some' to
        'http://127.0.0.1:5000/pdf/?q=%23other'.
        """

        parsed_referer_url = urlparse(referer_url)
        query_parameters = parse_qs(parsed_referer_url.query)

        tag_query = []

        for tag in query_parameters.get('tags', [''])[0].split(' '):
            if tag and tag != replace:
                tag_query.append(tag)
            elif tag and replace_with:
                tag_query.append(replace_with)

        query_parameters['tags'] = tag_query

        query_string = '&'.join(
            f'{key}={"+".join(query)}' for key, query in query_parameters.items() if query not in [[], ['']]
        )

        overview_url = reverse('pdf_overview')

        if query_string:
            overview_url = f'{overview_url}?{query_string}'

        return overview_url


class PdfProcessingServices:
    @classmethod
    def create_pdf(
        cls,
        name: str,
        owner: Profile,
        pdf_file: File,
        description: str = '',
        notes: str = '',
        tag_string: str = '',
        file_directory: str = '',
    ):
        pdf = Pdf.objects.create(
            name=name, description=description, notes=notes, file=pdf_file, file_directory=file_directory, owner=owner
        )

        # process with pdf libraries: add number of pages, thumbnail, preview, highlights and comments
        cls.process_with_pypdfium(pdf)
        cls.set_highlights_and_comments(pdf)

        # get unique tag names
        tag_names = Tag.parse_tag_string(tag_string)
        tags = TagServices.process_tag_names(tag_names, pdf.owner)

        pdf.tags.set(tags)

        return pdf

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
            logger.info(f'Could not process "{pdf.name}" of user "{pdf.owner.user.email}" with Pypdfium')
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
            logger.info(f'Could not extract thumbnail for "{pdf.name}" of user "{pdf.owner.user.email}"')
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

            pyreadium_pdf.close()

        except Exception as e:  # nosec # noqa
            logger.info(f'Could not extract highlights and comments for "{pdf.name}" of user "{pdf.owner.user.email}"')
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
    def export_annotations(cls, profile: Profile, kind: str, pdf: Pdf = None):
        """Export annotations to yaml. Annotations can be comments or highlights of a single or all pdfs of a user."""

        if pdf:
            if kind == 'comments':
                pdf_annotations = pdf.pdfcomment_set.all()
            else:
                pdf_annotations = pdf.pdfhighlight_set.all()
        else:
            if kind == 'comments':
                pdf_annotations = PdfComment.objects.filter(pdf__owner=profile).all()
            else:
                pdf_annotations = PdfHighlight.objects.filter(pdf__owner=profile).all()

        cls.export_annotations_to_yaml(pdf_annotations, str(profile.user.id))

    @classmethod
    def export_annotations_to_yaml(cls, annotations: QuerySet[PdfAnnotation], user_id: str):
        """Export the provided annotations to yaml."""

        export_path = cls.get_annotation_export_path(user_id)
        export_path.parent.mkdir(exist_ok=True)

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

        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)

        with open(export_path, 'wb') as f:
            yaml.dump(dict(serialized_annotations), f)

    @staticmethod
    def get_annotation_export_path(user_id: str):  # pragma: no cover
        """Get the annotation export path uf the specified user."""

        return MEDIA_ROOT / user_id / 'annotations' / 'annotations_export.yaml'

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

            delete_empty_dirs_after_rename_or_delete(pdf_current_file_name, pdf.owner.user.id)


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


def get_future_datetime(time_input: str) -> datetime | None:
    """
    Gets a datetime in the future from now based on the input. Input is in the format _d_h_m, e.g. 1d0h22m.
    If input is an empty string returns None
    """

    if not time_input:
        return None

    split_by_d = time_input.split('d')
    split_by_d_and_h = split_by_d[1].split('h')
    split_by_d_and_h_and_m = split_by_d_and_h[1].split('m')

    days = int(split_by_d[0])
    hours = int(split_by_d_and_h[0])
    minutes = int(split_by_d_and_h_and_m[0])

    now = datetime.now(timezone.utc)
    future_date = now + timedelta(days=days, hours=hours, minutes=minutes)

    return future_date


def create_name_from_file(file: File | Path) -> str:
    """
    Get the file name from the file name. Will remove the '.pdf' from the file name.
    """

    name = file.name
    split_name = name.rsplit(sep='.', maxsplit=1)

    if len(split_name) > 1 and str.lower(split_name[-1]) == 'pdf':
        name = split_name[0]

    return name


def create_unique_name_from_file(file: File, owner: Profile) -> str:
    """
    Get the file name from the file name. Will remove the '.pdf' from the file name. If there is already
    a pdf with the same name then it will add a random 8 characters long suffix.
    """

    name = create_name_from_file(file)

    existing_pdf = Pdf.objects.filter(owner=owner, name=name).first()

    # if pdf name is already existing add a random 8 characters long string
    if existing_pdf:
        name += f'_{str(uuid4())[:8]}'

    return name


def get_pdf_info_list(profile: Profile) -> list[tuple]:
    """
    Get the pdf info list of a profile. It contains information (name + file size) of each pdf of the profile. Each
    element is a tuple with (pdf name, pdf size).
    """

    pdf_info_list = []

    for pdf in profile.pdf_set.all():
        pdf_size = Path(pdf.file.path).stat().st_size
        pdf_info_list.append((pdf.name, pdf_size))

    return pdf_info_list
