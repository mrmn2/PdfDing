from datetime import datetime, timedelta, timezone
from uuid import uuid4

from django.contrib.auth.models import User
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from pdf.models.collection_models import Collection, CollectionError
from pdf.models.pdf_models import Pdf
from pdf.models.shared_models import SharedCollection, SharedPdf
from pdf.models.workspace_models import Workspace

newest_trans = _('Newest')
oldest_trans = _('Oldest')
name_asc_trans = _('Name Asc')
name_desc_trans = _('Name Desc')
NAGGING_INTERVAL_WEEKS = 2


def get_last_time_nagged_initial():  # pragma: no cover
    return datetime.now(tz=timezone.utc) - timedelta(weeks=5)


class Profile(models.Model):
    """The user profile model of PdfDing"""

    class DarkMode(models.TextChoices):
        SYSTEM = 'System', _('System')
        LIGHT = 'Light', _('Light')
        DARK = 'Dark', _('Dark')

    class PdfsPerPage(models.IntegerChoices):
        p_5 = 5, '5'
        p_10 = 10, '10'
        p_25 = 25, '25'
        p_50 = 50, '50'
        p_100 = 100, '100'

    class EnabledChoice(models.TextChoices):
        ENABLED = 'Enabled', _('Enabled')
        DISABLED = 'Disabled', _('Disabled')

    class PdfSortingChoice(models.TextChoices):
        NEWEST = 'Newest', newest_trans
        OLDEST = 'Oldest', oldest_trans
        NAME_ASC = 'Name_asc', name_asc_trans
        NAME_DESC = 'Name_desc', name_desc_trans
        MOST_VIEWED = 'Most_viewed', _('Most Viewed')
        LEAST_VIEWED = 'Least_viewed', _('Least Viewed')
        RECENTLY_VIEWED = 'Recently_viewed', _('Recently Viewed')

    class SharedPdfSortingChoice(models.TextChoices):
        NEWEST = 'Newest', newest_trans
        OLDEST = 'Oldest', oldest_trans
        NAME_ASC = 'Name_asc', name_asc_trans
        NAME_DESC = 'Name_desc', name_desc_trans

    class UserSortingChoice(models.TextChoices):
        NEWEST = 'Newest', newest_trans
        OLDEST = 'Oldest', oldest_trans
        EMAIL_ASC = 'Email_asc', _('Email Asc')
        EMAIL_DESC = 'Email_desc', _('Email Desc')

    class AnnotationsSortingChoice(models.TextChoices):
        NEWEST = 'Newest', newest_trans
        OLDEST = 'Oldest', oldest_trans

    class LayoutChoice(models.TextChoices):
        COMPACT = 'Compact', _('Compact')
        LIST = 'List', _('List')
        GRID = 'Grid', _('Grid')
        MINIMAL = 'Minimal', _('Minimal')

    class LanguageChoice(models.TextChoices):
        AUTO = 'Auto'
        ENGLISH = 'English'

    annotation_sorting = models.CharField(
        choices=AnnotationsSortingChoice, max_length=15, default=AnnotationsSortingChoice.NEWEST
    )
    current_collection_id = models.CharField(max_length=36, editable=False, blank=False)
    current_workspace_id = models.CharField(max_length=36, editable=False, blank=False)
    dark_mode = models.CharField(choices=DarkMode.choices, max_length=6, default=DarkMode.DARK)
    minutes_spent_reading = models.PositiveIntegerField(default=0, blank=False)
    layout = models.CharField(choices=LayoutChoice.choices, max_length=7, default=LayoutChoice.COMPACT)
    language = models.CharField(choices=LanguageChoice.choices, max_length=30, default=LanguageChoice.ENGLISH)
    last_time_nagged = models.DateTimeField(default=get_last_time_nagged_initial)
    pdf_inverted_mode = models.CharField(choices=EnabledChoice.choices, max_length=8, default=EnabledChoice.DISABLED)
    pdf_keep_screen_awake = models.CharField(
        choices=EnabledChoice.choices, max_length=8, default=EnabledChoice.DISABLED
    )
    pdf_sorting = models.CharField(choices=PdfSortingChoice, max_length=15, default=PdfSortingChoice.NEWEST)
    show_progress_bars = models.CharField(choices=EnabledChoice.choices, max_length=8, default=EnabledChoice.ENABLED)
    shared_pdf_sorting = models.CharField(
        choices=SharedPdfSortingChoice, max_length=15, default=SharedPdfSortingChoice.NEWEST
    )
    signatures = models.JSONField(default=dict)
    tags_open = models.BooleanField(default=False)
    tag_tree_mode = models.BooleanField(default=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_sorting = models.CharField(choices=UserSortingChoice, max_length=15, default=UserSortingChoice.NEWEST)

    def __str__(self):  # pragma: no cover
        return str(self.user.email)  # type: ignore

    @property
    def dark_mode_str(self) -> str:  # pragma: no cover
        """Return dark mode property so that it can be used in templates."""

        return str.lower(str(self.dark_mode))

    @property
    def current_workspace(self):
        """Return the current workspace associated of the profile."""

        return self.workspaces.get(id=self.current_workspace_id)

    @property
    def current_collection(self):
        """Return the current collection of the profile."""

        if self.current_collection_id == 'all':  # pragma: no cover
            raise CollectionError('Current collection not defined for collection ID "all"!')

        return self.collections.get(id=self.current_collection_id)

    @property
    def current_collection_name(self):
        """Return the name of the current collection"""

        if self.current_collection_id == 'all':
            current_collection_name = 'All'
        else:
            current_collection_name = self.current_collection.name

        return current_collection_name

    @property
    def all_pdfs(self) -> QuerySet:
        """Return all PDFs of all workspaces the user has access to."""

        collections = Collection.objects.filter(workspace__in=self.workspaces)
        pdfs = Pdf.objects.filter(collection__in=collections)

        return pdfs

    @property
    def current_pdfs(self) -> QuerySet:
        """Return all PDFs of the current collections (all or single)."""

        if self.current_collection_id == 'all':
            pdfs = Pdf.objects.filter(collection__in=self.current_workspace.collections)
        else:
            pdfs = Pdf.objects.filter(collection_id=self.current_collection_id)

        return pdfs

    @property
    def all_shared_pdfs(self) -> QuerySet:
        """Return all shared PDFs of all workspaces the profile has access to."""

        shared_pdfs = SharedPdf.objects.filter(pdf__in=self.all_pdfs)

        return shared_pdfs

    @property
    def current_shared_pdfs(self) -> QuerySet:
        """Return all shared PDFs of the current collection (all or single)."""

        shared_pdfs = SharedPdf.objects.filter(pdf__in=self.current_pdfs)

        return shared_pdfs

    @property
    def all_collections(self) -> QuerySet:
        """Return all collections of all workspaces the user has access to."""

        collections = Collection.objects.filter(workspace__in=self.workspaces)

        return collections

    @property
    def all_shared_collections(self) -> QuerySet:
        """Return all shared collections of all workspaces the profile has access to."""

        shared_pdfs = SharedCollection.objects.filter(collection__in=self.all_collections)

        return shared_pdfs

    @property
    def tags(self) -> QuerySet:
        """Return all tags associated with the profile."""

        return self.current_workspace.tag_set.all()

    @property
    def workspaces(self) -> QuerySet:
        """Return all workspaces associated with the profile."""

        workspaces = Workspace.objects.filter(workspaceuser__user=self.user)

        return workspaces

    @property
    def collections(self) -> QuerySet:
        """Return all collections associated with the profile."""

        workspace = self.workspaces.get(id=self.current_workspace_id)

        return workspace.collections

    @property
    def hours_spent_reading(self) -> int:
        """Return the hours spent reading PDFs"""

        return self.minutes_spent_reading // 60

    @property
    def mfa_activated(self) -> bool:
        """Check if multi factor authentication is activated"""

        try:
            if self.user.authenticator_set.count():
                return True
            else:
                return False
        except AttributeError:  # pragma: no cover
            return False

    @property
    def language_code(self) -> str:  # pragma: no cover
        """Return the language code of the selected language"""

        language_codes = {'Auto': 'auto', 'English': 'en'}

        return language_codes[self.language]

    @property
    def needs_nagging(self):
        """
        Check if a user needs to be nagged. This is used for nagging users to fill out a survey
        or support PdfDing through donations.
        """

        if (datetime.now(tz=timezone.utc) - self.last_time_nagged).days > NAGGING_INTERVAL_WEEKS * 7:
            return True
        else:
            return False

    @property
    def uses_social(self):
        """Flag if user is a OIDC account"""

        uses_social = self.user.socialaccount_set.exists()

        return uses_social

    def has_access_to_workspace(self, workspace_id: str) -> bool:
        """Check if the profile has access to the specified workspace"""

        if self.workspaces.filter(id=workspace_id).count():
            return True
        else:
            return False

    def get_items_per_page(self, page: str) -> int:  # pragma: no cover
        """Get the number of items of overview paginations"""

        if page == 'pdf_overview':
            if self.layout == self.LayoutChoice.MINIMAL:
                return 30
            else:
                return 12
        else:
            return 20


class PdfReadingInformation(models.Model):
    """
    Model for storing information related to reading a PDF of a single profile. The
    information currently includes the current page and the last time the pdf was opened.
    """

    last_viewed_date = models.DateTimeField(blank=False, editable=False)
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    current_page = models.IntegerField(blank=False)
    pdf = models.ForeignKey(Pdf, on_delete=models.CASCADE, blank=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=False)
    views = models.IntegerField(blank=False)
