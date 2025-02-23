from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """The user profile model of PdfDing"""

    class DarkMode(models.TextChoices):
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

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # set dummy default colors, will be overwritten
    dark_mode = models.CharField(choices=DarkMode.choices, max_length=5, default=DarkMode.DARK)
    theme_color = models.CharField(choices=ThemeColor.choices, max_length=6, default=ThemeColor.RED)
    custom_theme_color = models.CharField(max_length=7, default='#ffa385')
    custom_theme_color_secondary = models.CharField(max_length=7, default='#cc826a')
    custom_theme_color_tertiary_1 = models.CharField(max_length=7, default='#99614f')
    custom_theme_color_tertiary_2 = models.CharField(max_length=7, default='#ffc7b5')
    pdf_inverted_mode = models.CharField(choices=EnabledChoice.choices, max_length=8, default=EnabledChoice.DISABLED)
    pdfs_per_page = models.IntegerField(choices=PdfsPerPage.choices, default=PdfsPerPage.p_25)
    pdf_sorting = models.CharField(choices=PdfSortingChoice, max_length=15, default=PdfSortingChoice.NEWEST)
    shared_pdf_sorting = models.CharField(
        choices=SharedPdfSortingChoice, max_length=15, default=SharedPdfSortingChoice.NEWEST
    )
    show_progress_bars = models.CharField(choices=EnabledChoice.choices, max_length=8, default=EnabledChoice.ENABLED)
    show_thumbnails = models.CharField(choices=EnabledChoice.choices, max_length=8, default=EnabledChoice.DISABLED)
    tags_open = models.BooleanField(default=False)
    tag_tree_mode = models.BooleanField(default=True)
    user_sorting = models.CharField(choices=UserSortingChoice, max_length=15, default=UserSortingChoice.NEWEST)

    def __str__(self):  # pragma: no cover
        return str(self.user.email)

    @property
    def dark_mode_str(self):  # pragma: no cover
        """Return dark mode property so that it can be used in templates."""

        return str.lower(str(self.dark_mode))
