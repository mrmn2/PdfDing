from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet


def get_last_time_nagged_initial():  # pragma: no cover
    return datetime.now(tz=timezone.utc) - timedelta(weeks=5)


class Profile(models.Model):
    """The user profile model of PdfDing"""

    class DarkMode(models.TextChoices):
        SYSTEM = 'System'
        LIGHT = 'Light'
        DARK = 'Dark'
        CREME = 'Creme'

    class PdfsPerPage(models.IntegerChoices):
        p_5 = 5, '5'
        p_10 = 10, '10'
        p_25 = 25, '25'
        p_50 = 50, '50'
        p_100 = 100, '100'

    class ThemeColor(models.TextChoices):
        GREEN = 'Green'
        BLUE = 'Blue'
        GRAY = 'Gray'
        RED = 'Red'
        PINK = 'Pink'
        ORANGE = 'Orange'
        BROWN = 'Brown'
        CUSTOM = 'Custom'

    class EnabledChoice(models.TextChoices):
        ENABLED = 'Enabled'
        DISABLED = 'Disabled'

    class PdfSortingChoice(models.TextChoices):
        NEWEST = 'Newest'
        OLDEST = 'Oldest'
        NAME_ASC = 'Name_asc'
        NAME_DESC = 'Name_desc'
        MOST_VIEWED = 'Most_viewed'
        LEAST_VIEWED = 'Least_viewed'
        RECENTLY_VIEWED = 'Recently_viewed'

    class SharedPdfSortingChoice(models.TextChoices):
        NEWEST = 'Newest'
        OLDEST = 'Oldest'
        NAME_ASC = 'Name_asc'
        NAME_DESC = 'Name_desc'

    class UserSortingChoice(models.TextChoices):
        NEWEST = 'Newest'
        OLDEST = 'Oldest'
        EMAIL_ASC = 'Email_asc'
        EMAIL_DESC = 'Email_desc'

    class AnnotationsSortingChoice(models.TextChoices):
        NEWEST = 'Newest'
        OLDEST = 'Oldest'

    class LayoutChoice(models.TextChoices):
        COMPACT = 'Compact'
        LIST = 'List'
        GRID = 'Grid'

    annotation_sorting = models.CharField(
        choices=AnnotationsSortingChoice, max_length=15, default=AnnotationsSortingChoice.NEWEST
    )
    # set dummy default colors, will be overwritten in users/signals.py
    custom_theme_color = models.CharField(max_length=7, default='#ffa385')
    custom_theme_color_secondary = models.CharField(max_length=7, default='#cc826a')
    dark_mode = models.CharField(choices=DarkMode.choices, max_length=6, default=DarkMode.DARK)
    layout = models.CharField(choices=LayoutChoice.choices, max_length=7, default=LayoutChoice.COMPACT)
    last_time_nagged = models.DateTimeField(default=get_last_time_nagged_initial)
    number_of_pdfs = models.IntegerField(default=0)
    pdf_inverted_mode = models.CharField(choices=EnabledChoice.choices, max_length=8, default=EnabledChoice.DISABLED)
    pdf_keep_screen_awake = models.CharField(
        choices=EnabledChoice.choices, max_length=8, default=EnabledChoice.DISABLED
    )
    pdf_sorting = models.CharField(choices=PdfSortingChoice, max_length=15, default=PdfSortingChoice.NEWEST)
    pdfs_total_size = models.IntegerField(default=0)
    show_progress_bars = models.CharField(choices=EnabledChoice.choices, max_length=8, default=EnabledChoice.ENABLED)
    shared_pdf_sorting = models.CharField(
        choices=SharedPdfSortingChoice, max_length=15, default=SharedPdfSortingChoice.NEWEST
    )
    signatures = models.JSONField(default=dict)
    tags_open = models.BooleanField(default=False)
    tag_tree_mode = models.BooleanField(default=True)
    theme_color = models.CharField(choices=ThemeColor.choices, max_length=6, default=ThemeColor.RED)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_sorting = models.CharField(choices=UserSortingChoice, max_length=15, default=UserSortingChoice.NEWEST)

    def __str__(self):  # pragma: no cover
        return str(self.user.email)  # type: ignore

    @property
    def dark_mode_str(self) -> str:  # pragma: no cover
        """Return dark mode property so that it can be used in templates."""

        return str.lower(str(self.dark_mode))

    @property
    def needs_nagging(self):
        """
        Check if a user needs to be nagged to sponsor the project. Only nags once every 8 weeks. Users
        of the Supporter Edition will never be nagged.
        """

        if not settings.SUPPORTER_EDITION and (datetime.now(tz=timezone.utc) - self.last_time_nagged).days > 7 * 8:
            return True
        else:
            return False

    @property
    def pdfs_total_size_with_unit(self):
        """Return the size of all PDFs with the units KB, MB, GB depending on the size."""

        pdfs_total_size = self.pdfs_total_size

        if self.pdfs_total_size < 10**6:
            return f'{round(pdfs_total_size / 1000, 2)} KB'
        elif self.pdfs_total_size < 10**9:
            return f'{round(pdfs_total_size / (10 ** 6), 2)} MB'
        else:
            return f'{round(pdfs_total_size / (10 ** 9), 2)} GB'

    @property
    def pdfs(self) -> QuerySet:
        """Return all PDFs associated with the profile."""

        return self.pdf_set.all()

    @property
    def shared_pdfs(self) -> QuerySet:
        """Return all shared PDFs associated with the profile."""

        return self.sharedpdf_set.all()

    @property
    def tags(self) -> QuerySet:
        """Return all tags associated with the profile."""

        return self.tag_set.all()
