import re

from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm
from users.models import Profile


class EmailForm(ModelForm):
    """The form for changing the email address."""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email']


class PdfsPerPageForm(ModelForm):
    """The form for setting the pdfs per page"""

    class Meta:
        model = Profile
        fields = ['pdfs_per_page']


class ThemeForm(ModelForm):
    """The form for setting dark mode"""

    class Meta:
        model = Profile
        fields = ['dark_mode', 'theme_color']


class PdfInvertedForm(ModelForm):
    """The form for setting the inverted PDF color mode"""

    class Meta:
        model = Profile
        fields = ['pdf_inverted_mode']


class ProgressBarForm(ModelForm):
    """The form for setting progress bars"""

    class Meta:
        model = Profile
        fields = ['show_progress_bars']


class TagsTreeModeForm(ModelForm):
    """The form for setting tag tree mode"""

    class Meta:
        model = Profile
        fields = ['tags_tree_mode']


class CustomThemeColorForm(ModelForm):
    """The form for setting dark mode"""

    class Meta:
        model = Profile
        fields = ['custom_theme_color']

    def clean_custom_theme_color(self) -> str:
        """Check that the provided max views are a positive integer"""

        return clean_hex_color(self.cleaned_data['custom_theme_color'])


def clean_hex_color(color: str) -> str:
    """Check that the provided max views are a positive integer"""

    if not re.match(r'^#[A-Fa-f0-9]{6}$', color):
        raise forms.ValidationError('Only valid hex colors are allowed! E.g.: #ffa385.')

    return str.lower(color)
