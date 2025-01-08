from datetime import datetime, timezone
from uuid import uuid4

import markdown
import nh3
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db import models
from django.utils.safestring import mark_safe
from users.models import Profile


class Tag(models.Model):
    """The model for the tags used for organizing PDF files."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, null=True, blank=False)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):  # pragma: no cover
        return str(self.name)

    @staticmethod
    def parse_tag_string(tag_string: str):
        if not tag_string:
            return []

        for forbidden_char in ['#', '&', '+']:
            tag_string = tag_string.replace(forbidden_char, '')

        names = tag_string.strip().split(' ')
        # remove empty names, sanitize remaining names
        names = [name.strip() for name in names if name]
        # remove duplicates
        names = [name.lower() for name in set(names)]

        return sorted(names)


def get_file_path(instance, _):
    """
    Get the file path for a PDF. File paths are user_id/file_id.pdf

    User uploaded files will always be placed inside MEDIA_ROOT.
    """

    file_name = f'{instance.id}.pdf'
    file_path = '/'.join([str(instance.owner.user.id), file_name])

    return str(file_path)


def get_qrcode_file_path(instance, _):
    """Get the file path for the qr code of a shared PDF."""

    file_name = f'{instance.id}.svg'
    file_path = '/'.join([str(instance.owner.user.id), 'qr', file_name])

    return str(file_path)


class Pdf(models.Model):
    """Model for the pdf files."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=False)
    name = models.CharField(max_length=150, null=True, blank=False)
    file = models.FileField(upload_to=get_file_path, blank=False)
    description = models.TextField(null=True, blank=True, help_text='Optional')
    notes = models.TextField(null=True, blank=True, help_text='Optional, supports Markdown')
    creation_date = models.DateTimeField(blank=False, editable=False, auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True)
    current_page = models.IntegerField(default=1)
    views = models.IntegerField(default=0)
    last_viewed_date = models.DateTimeField(
        blank=False, editable=False, default=datetime(2000, 1, 1, tzinfo=timezone.utc)
    )
    number_of_pages = models.IntegerField(default=-1)
    starred = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name  # pragma: no cover

    @property
    def natural_age(self) -> str:
        """
        Get the natural age of a file. This converts the creation date to a natural age,
        e.g: 2 minutes, 1 hour,  2 months, etc
        """

        natural_time = naturaltime(self.creation_date)

        if ',' in natural_time:
            natural_time = natural_time.split(sep=', ')[0]
        else:
            natural_time = natural_time.replace(' ago', '')

        # naturaltime will include space characters that will cause failed unit tests
        # splitting and joining fixes that
        return ' '.join(natural_time.split())

    @property
    def progress(self) -> int:
        """Get read progress of the pdf in percent"""

        progress = round(100 * self.current_page_for_progress / self.number_of_pages)

        return min(progress, 100)

    @property
    def current_page_for_progress(self) -> int:
        """
        Get the current page for progress calculations. If there are zero views the current page should be zero. If
        there are views we use the current page of the pdf. If the current page is negative for some reason we also
        return 0
        """

        if self.views == 0:
            current_page = 0
        else:
            current_page = self.current_page

        return max(current_page, 0)

    @property
    def notes_html(self) -> str:
        """Converts markdown notes to html and sanitizes them, so that they can be displayed in the PDF overview."""

        notes_html = markdown.markdown(str(self.notes), extensions=['fenced_code', 'nl2br'])
        cleaned_notes_html = nh3.clean(
            notes_html,
            attributes=MarkdownHelper.get_allowed_markdown_attributes(),
            tags=MarkdownHelper.get_allowed_markdown_tags(),
        )

        # bandit will report a vulnerability because of the usage of mark_safe of XSS and cross-site scripting
        # vulnerabilities. since nh3 is used to clean the generated markdown we can ignore the warning
        return mark_safe(cleaned_notes_html)  # nosec

    @property
    def file_id(self) -> str:
        """
        Get the file id. This will be the name of the file without the user id. E.g.: 1/123456789 -> 123456789.

        We cannot use the id of the pdf in order to be backwards compatible as in earlier versions a UUID was used
        instead of the pdf id.
        """

        user_id_file_id = self.file.name.replace('.pdf', '')
        file_id = user_id_file_id.replace(f'{str(self.owner.user.id)}/', '')

        return file_id


class SharedPdf(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=False)
    pdf = models.ForeignKey(Pdf, on_delete=models.CASCADE, blank=False)
    name = models.CharField(max_length=150, null=True, blank=False)
    # the qr code file
    file = models.FileField(upload_to=get_qrcode_file_path, blank=False)
    description = models.TextField(null=True, blank=True, help_text='Optional')
    creation_date = models.DateTimeField(blank=False, editable=False, auto_now_add=True)
    views = models.IntegerField(default=0)
    max_views = models.IntegerField(null=True, blank=True, help_text='Optional')
    password = models.CharField(max_length=128, null=True, blank=True, help_text='Optional')
    expiration_date = models.DateTimeField(null=True, blank=True)
    deletion_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name  # pragma: no cover

    @property
    def inactive(self):
        """The shared pdf weather is inactive. This will consider the expiration date and max views."""

        return (self.max_views and self.views >= self.max_views) or (
            self.expiration_date and datetime.now(timezone.utc) >= self.expiration_date
        )

    @property
    def deleted(self):
        """The shared pdf weather is deleted. This will consider the deletion date."""

        return self.deletion_date and datetime.now(timezone.utc) >= self.deletion_date

    @property
    def deletes_in_string(self) -> str:  # pragma: no cover
        """
        Get the natural time representation of the deletion date compared to the current datetime.
        """

        return self.get_natural_time_future(self.deletion_date, 'deletes', 'deleted')

    @property
    def expires_in_string(self) -> str:  # pragma: no cover
        """
        Get the natural time representation of the expiration date compared to the current datetime.
        """

        return self.get_natural_time_future(self.expiration_date, 'expires', 'expired')

    @staticmethod
    def get_natural_time_future(date: models.DateTimeField, context_present: str, context_past: str) -> str:
        """
        Get the natural time representation of a date compared to the current datetime. Will return a string of the
        format <context> in <natural time>, e.g deletes in 1 day.
        """

        if date:
            natural_time = naturaltime(date)
            if date < datetime.now(timezone.utc):
                return_string = context_past

            else:
                if ',' in natural_time:
                    natural_time = natural_time.split(sep=', ')[0]

                natural_time = natural_time.replace(' from now', '')

                return_string = f'{context_present} in {natural_time}'
        else:
            return_string = f'{context_present} never'

        # replace weird string so test have no problems
        return_string = return_string.replace(u'\xa0', u' ')

        return return_string

    @property
    def views_string(self) -> str:
        """
        Get the view string for the frontend. If ax views is set returns <views>/<max_views> Views
        else <view> Views
        """

        if self.max_views:
            return f'{self.views}/{self.max_views} Views'
        else:
            return f'{self.views} Views'


class MarkdownHelper:  # pragma: no cover
    @staticmethod
    def get_allowed_markdown_tags() -> set[str]:
        """Get the html tags that are allowed when sanitizing the markdown html"""

        # fmt: off
        markdown_tags = {
            "h1", "h2", "h3", "h4", "h5", "h6",
            "b", "i", "strong", "em", "tt",
            "p", "br",
            "span", "div", "blockquote", "code", "pre", "hr",
            "ul", "ol", "li", "dd", "dt",
            "a",
            "sub", "sup",
        }
        # fmt: on

        return set(markdown_tags)

    @staticmethod
    def get_allowed_markdown_attributes() -> dict[str, set[str]]:
        """Get the html attributes that are allowed when sanitizing the markdown html"""

        markdown_attrs = {"*": {"id"}, "a": {"href", "alt", "title"}}

        return markdown_attrs
