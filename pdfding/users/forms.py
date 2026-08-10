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
