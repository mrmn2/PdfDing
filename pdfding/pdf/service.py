from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.forms import ValidationError
from django.http import Http404, HttpRequest
from users.models import Profile

from .models import Pdf, Tag


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


def get_tag_dict(profile: Profile) -> dict[str, list[str]]:
    """
    Get the tag dict used for displaying the tags in the pdf overview.

    Keys of the returned dict are the first characters, values the tags without the first character, e.g:
    {'b': ['anana', 'read'], 't': ['ag_1', 'ag_3']}. This format was chosen, so it is possible to capitalize, change
     the font weight and color the first occurrence of character. In the frontend the example will look:

     **B**anana bread
     **T**ag_1, tag_3
    """

    # relies on deterministic 3.7+ key ordering
    tags = profile.tag_set.all().order_by('name')
    tag_dict = defaultdict(list)

    for tag in tags:
        if tag.pdf_set.all():
            tag_dict[tag.name[0]].append(tag)

    # needs to be a normal dict, so that the template can handle it
    return dict(tag_dict)


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


def create_name_from_file(file: File) -> str:
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

    referer_url_split = referer_url.split('/?q=', maxsplit=1)

    if len(referer_url_split) == 2:
        if not replace_with:
            replace_with = ''
        else:
            replace_with = f'%23{replace_with}'

        query = referer_url_split[1]
        query = query.replace(f'%23{replace}', replace_with)

        referer_url = f'{referer_url_split[0]}/?q={query}'

    return referer_url
