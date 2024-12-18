import traceback
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from logging import getLogger
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.db.models.functions import Lower
from django.forms import ValidationError
from django.http import Http404, HttpRequest
from django.urls import reverse
from pdf.models import Pdf, Tag
from pypdf import PdfReader
from users.models import Profile

logger = getLogger(__file__)


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


def get_tag_dict(profile: Profile) -> dict[str, dict]:
    """
    Get the tag dict used for displaying the tags in the pdf overview. Key: name of the tag. Value: Information
    about the tag (level, has_children, tree_only, parent)
    """

    # it is important that the tags are sorted. As parent tags need come before children,
    # e.g. "programming" before "programming/python"
    tags = profile.tag_set.all().order_by(Lower('name'))
    tag_dict = OrderedDict()

    for tag in tags:
        tag_split = tag.name.split('/', maxsplit=2)
        current = ''
        words = []

        for level, word in enumerate(tag_split):
            prev = current
            words.append(word)
            current = '/'.join(words)

            if level:
                tag_dict[prev]['has_children'] = True

            if current not in tag_dict:
                if level == len(tag_split) - 1:
                    tree_only = False
                else:
                    tree_only = True

                tag_dict[current] = {'level': level, 'has_children': False, 'tree_only': tree_only, 'parent': prev}

    return tag_dict


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


def set_number_of_pages(pdf: Pdf):
    """Set the number of pages in a pdf file. If the extraction is not successful, it will leave the default value."""

    try:
        reader = PdfReader(pdf.file.path)
        pdf.number_of_pages = reader.get_num_pages()
        pdf.save()
    except Exception as e:  # nosec # noqa
        logger.info(f'Could not determine number of pages for "{pdf.name}" of user "{pdf.owner.user.email}"')
        logger.info(traceback.format_exc())


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
