import re
from datetime import datetime, timezone
from uuid import uuid4

import markdown
import nh3
from core.settings import MEDIA_ROOT
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db import models
from django.db.models import DateTimeField
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from users.models import Profile


class Tag(models.Model):
    """The model for the tags used for organizing PDF files."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, null=True, blank=False)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):  # pragma: no cover
        return str(self.name)

    @staticmethod
    def parse_tag_string(tag_string: str) -> list[str]:
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


def get_file_path(instance, _) -> str:
    """
    Get the file path for a PDF inside the media root based on the pdf name.File paths are user_id/some/dir/name.pdf.
    This function will also replace any "/" in the pdf name and will make  sure there are no duplicate file names.
    """

    # replace any space char with _
    file_name = re.sub(r'\s+', '_', instance.name)
    file_name = file_name.replace('/', '_')
    file_name = str.lower(file_name)
    # remove non alphanumerical characters
    file_name = slugify(file_name, allow_unicode=True)

    sub_dir = instance.file_directory

    # make sure file name is not empty
    if not file_name:
        file_name = 'pdf'

    file_name = f'{file_name}.pdf'

    if sub_dir:
        sub_dir.strip()
        file_path = '/'.join([str(instance.owner.user.id), 'pdf', sub_dir, file_name])
    else:
        file_path = '/'.join([str(instance.owner.user.id), 'pdf', file_name])

    existing_pdf = Pdf.objects.filter(file=file_path).first()

    # make sure there each file path is unique
    if existing_pdf and str(existing_pdf.id) != str(instance.id):
        file_path = file_path.replace('.pdf', f'_{str(uuid4())[:8]}.pdf')

    return file_path


def delete_empty_dirs_after_rename_or_delete(pdf_current_file_name: str, user_id: str) -> None:
    """
    Delete empty directories in the users media/pdf directory that appear as a result of renaming or deleting pdfs.
    """

    current_path = MEDIA_ROOT / pdf_current_file_name

    pdf_current_file_name_adjusted = pdf_current_file_name.replace(f'{user_id}/pdf/', '')

    for _ in pdf_current_file_name_adjusted.split('/'):
        current_parent_path = current_path.parent
        sub_paths = [sub_path for sub_path in current_parent_path.iterdir()]

        if not sub_paths:
            current_parent_path.rmdir()
            current_path = current_parent_path
        else:
            break


def get_thumbnail_path(instance, _) -> str:
    """Get the file path for the thumbnail of a PDF."""

    file_name = f'thumbnails/{instance.id}.png'
    file_path = '/'.join([str(instance.owner.user.id), file_name])

    return str(file_path)


def get_preview_path(instance, _) -> str:
    """Get the file path for the preview of a PDF."""

    file_name = f'previews/{instance.id}.png'
    file_path = '/'.join([str(instance.owner.user.id), file_name])

    return str(file_path)


def convert_to_natural_age(creation_date: DateTimeField) -> str:
    """Convert the creation date into a natural age, e.g: 2 minutes, 1 hour,  2 months, etc"""

    natural_time = naturaltime(creation_date)

    if ',' in natural_time:
        natural_time = natural_time.split(sep=', ')[0]
    else:
        natural_time = natural_time.replace(' ago', '')

    # naturaltime will include space characters that will cause failed unit tests
    # splitting and joining fixes that
    return ' '.join(natural_time.split())


class Pdf(models.Model):
    """Model for the pdf files."""

    archived = models.BooleanField(default=False)
    creation_date = models.DateTimeField(blank=False, editable=False, auto_now_add=True)
    current_page = models.IntegerField(default=1)
    description = models.TextField(null=True, blank=True, help_text='Optional')
    file_directory = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        help_text='Optional, save file in a sub directory of the pdf directory, e.g: important/pdfs',
    )
    file = models.FileField(upload_to=get_file_path, max_length=500, blank=False)
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    last_viewed_date = models.DateTimeField(
        blank=False, editable=False, default=datetime(2000, 1, 1, tzinfo=timezone.utc)
    )
    name = models.CharField(max_length=150, null=True, blank=False)
    notes = models.TextField(null=True, blank=True, help_text='Optional, supports Markdown')
    number_of_pages = models.IntegerField(default=-1)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=False)
    preview = models.FileField(upload_to=get_preview_path, null=True, blank=False)
    revision = models.IntegerField(default=0)
    starred = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, blank=True)
    thumbnail = models.FileField(upload_to=get_thumbnail_path, null=True, blank=False)
    views = models.IntegerField(default=0)

    def __str__(self) -> str:
        return self.name  # pragma: no cover

    def save(self, *args, **kwargs) -> None:
        # only update profile pdf stats if pdf object is created
        profile = self.owner
        profile_needs_saving = False

        if self._state.adding:
            profile.number_of_pdfs += 1
            try:
                profile.pdfs_total_size += self.file.size
            except (FileNotFoundError, ValueError):
                pass

            profile_needs_saving = True

        super().save(*args, **kwargs)

        if profile_needs_saving:
            profile.save()

    def delete(self, *args, **kwargs) -> None:
        # update profile pdf stats
        profile = self.owner
        profile.number_of_pdfs -= 1

        if not profile.number_of_pdfs:
            profile.pdfs_total_size = 0
        else:
            try:
                profile.pdfs_total_size -= self.file.size
            except (FileNotFoundError, ValueError):
                pass

        # clean up file directory if needed
        file_directory = self.file_directory
        file_name = self.file.name
        user_id = self.owner.user.id

        super().delete(*args, **kwargs)

        if file_directory:
            delete_empty_dirs_after_rename_or_delete(file_name, user_id)

        profile.save()

    @property
    def natural_age(self) -> str:  # pragma: no cover
        """
        Get the natural age of a file. This converts the creation date to a natural age,
        e.g: 2 minutes, 1 hour,  2 months, etc
        """

        return convert_to_natural_age(self.creation_date)

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


class PdfAnnotation(models.Model):
    """Model for the base pdf annotation"""

    creation_date = models.DateTimeField(null=True, blank=False, editable=False)
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    page = models.IntegerField(null=True, blank=False)
    pdf = models.ForeignKey(Pdf, on_delete=models.CASCADE, blank=False)
    text = models.TextField(null=True, blank=False)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.text  # pragma: no cover

    @property
    def natural_age(self) -> str:  # pragma: no cover
        """
        Get the natural age of a file. This converts the creation date to a natural age,
        e.g: 2 minutes, 1 hour,  2 months, etc
        """

        return convert_to_natural_age(self.creation_date)


class PdfComment(PdfAnnotation):
    """Model for the pdf comments."""


class PdfHighlight(PdfAnnotation):
    """Model for the pdf highlights."""


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
