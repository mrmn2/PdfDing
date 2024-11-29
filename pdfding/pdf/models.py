from datetime import datetime, timezone
from uuid import uuid4

from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db import models
from django.db.models import DateTimeField
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

        names = tag_string.strip().split(' ')
        # remove empty names, sanitize remaining names
        names = [name.strip() for name in names if name]
        # remove duplicates
        names = [name.replace('#', '').lower() for name in set(names)]

        return sorted(names)


def get_file_path(instance, _):
    """
    Get the file path for a PDF by generating a UUID and using the user id. File paths are user_id/<uuid>.pdf

    User uploaded files will always be placed inside MEDIA_ROOT.
    """

    file_name = f'{uuid4()}.pdf'
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
    creation_date = models.DateTimeField(blank=False, editable=False, auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True)
    current_page = models.IntegerField(default=1)
    views = models.IntegerField(default=0)
    last_viewed_date = models.DateTimeField(
        blank=False, editable=False, default=datetime(2000, 1, 1, tzinfo=timezone.utc)
    )
    number_of_pages = models.IntegerField(default=1)

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

        progress = round(100 * self.current_page / self.number_of_pages)

        return min(progress, 100)


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
    def get_natural_time_future(date: DateTimeField, context_present: str, context_past: str) -> str:
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
