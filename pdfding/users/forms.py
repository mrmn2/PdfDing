import re

from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm
from users.models import Profile


class GenericUserFieldForm(ModelForm):
    pass


def create_user_field_form(user_fields: list[str]):
    """
    Creates a user form with the specified fields.

    E.g. create_user_field_form('pdfs_per_page') will create the form for changing the 'pdfs_per_page' setting.
    """

    class UserFieldForm(GenericUserFieldForm):
        class Meta:
            model = Profile
            fields = user_fields

    return UserFieldForm


class EmailForm(ModelForm):
    """The form for changing the email address."""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email']


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
