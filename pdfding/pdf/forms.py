import re

import magic
from django import forms
from django.contrib.auth.hashers import check_password, make_password

# from django.core.exceptions import ValidationError
from django.core.files import File

from .models import Pdf, SharedPdf, Tag


class AddForm(forms.ModelForm):
    """Class for creating the form for adding PDFs."""

    tag_string = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add Tags'}),
        help_text='Enter any number of tags separated by space and without the hash (#). '
        'If a tag does not exist it will be automatically created.',
    )

    use_file_name = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Pdf
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Add PDF Name'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add Description'}),
            'file': forms.ClearableFileInput(attrs={'accept': 'application/pdf'}),
        }

        fields = ['name', 'description', 'file']

    def __init__(self, *args, **kwargs):
        """
        Adds the owner profile to the form. This is done, so we can check if the owner already has
        a PDF with the provided name in clean_name.
        """

        self.owner = kwargs.pop('owner', None)

        super(AddForm, self).__init__(*args, **kwargs)

    def clean(self):
        if not self.owner:
            raise forms.ValidationError('Owner is missing!')

        return self.cleaned_data

    def clean_name(self) -> str:
        """
        Clean the submitted pdf name. Removes trailing and multiple whitespaces. Also checks if the user already
        has an uploaded PDF with the same name.
        """

        pdf_name = CleanHelpers.clean_name(self.cleaned_data['name'])

        existing_pdf = Pdf.objects.filter(owner=self.owner, name=pdf_name).first()

        # only raise validation error if name is not the dummy placeholder from the frontend
        # otherwise it will be replaced by the filename in "clean".
        if pdf_name != 'bb36974a-3792-47c5-96cc-c79adb87cf82' and existing_pdf:
            raise forms.ValidationError('A PDF with this name already exists!')

        return pdf_name

    def clean_file(self) -> File:  # pragma: no cover
        """Clean the submitted pdf file. Checks if the file is a pdf."""

        return CleanHelpers.clean_file(self.cleaned_data['file'])


class MultipleFileInput(forms.ClearableFileInput):  # pragma: no cover
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):  # pragma: no cover
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class BulkAddForm(forms.Form):
    file = MultipleFileField(
        required=True,
        widget=MultipleFileInput(attrs={'accept': 'application/pdf'}),
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add Description'}),
        help_text='Optional',
    )

    tag_string = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add Tags'}),
        help_text='Enter any number of tags separated by space and without the hash (#). '
        'If a tag does not exist it will be automatically created.',
    )

    def __init__(self, *args, **kwargs):
        """
        Adds the owner profile to the form. This is done, so we can check if the owner already has
        a PDF with the provided name in clean_name.
        """

        self.owner = kwargs.pop('owner', None)

        super(BulkAddForm, self).__init__(*args, **kwargs)

    def clean(self):
        if not self.owner:
            raise forms.ValidationError('Owner is missing!')

        return self.cleaned_data

    def clean_file(self):
        for file in self.cleaned_data['file']:
            CleanHelpers.clean_file(file)


class DescriptionForm(forms.ModelForm):
    """Form for changing the description of a PDF."""

    class Meta:
        model = Pdf
        fields = ['description']


class NameForm(forms.ModelForm):
    """Form for changing the name of a PDF."""

    class Meta:
        model = Pdf
        fields = ['name']

    def clean_name(self) -> str:  # pragma: no cover
        """Clean the submitted pdf name. Removes trailing and multiple whitespaces."""
        pdf_name = CleanHelpers.clean_name(self.cleaned_data['name'])

        return pdf_name


class PdfTagsForm(forms.ModelForm):
    """Form for changing the tags of a PDF."""

    tag_string = forms.CharField(widget=forms.TextInput())

    class Meta:
        model = Pdf
        fields = []


class ShareForm(forms.ModelForm):
    """Class for creating the form for sharing PDFs."""

    expiration_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Expire in'}),
        help_text='Optional | e.g. 1d0h22m to expire in 1 day, 0 hours and 22 minutes.',
    )

    deletion_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Delete in'}),
        help_text='Optional | e.g. 1d0h22m to delete in 1 day, 0 hours and 22 minutes.',
    )

    class Meta:
        model = SharedPdf
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Add Share Name'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a private description'}),
            'max_views': forms.TextInput(attrs={'placeholder': 'Maximum number of views'}),
            'password': forms.PasswordInput(attrs={'placeholder': 'Protect the share with a password'}),
        }

        fields = ['name', 'description', 'password', 'max_views']

    def __init__(self, *args, **kwargs):
        """
        Adds the owner profile to the form. This is done, so we can check if the owner already has
        a PDF with the provided name in clean_name.
        """

        self.owner = kwargs.pop('owner', None)

        super(ShareForm, self).__init__(*args, **kwargs)

    def clean(self):
        if not self.owner:
            raise forms.ValidationError('Owner is missing!')

        return self.cleaned_data

    def clean_name(self) -> str:
        """
        Clean the submitted share name. Removes trailing and multiple whitespaces. Also checks if the user already
        has a share with the same name.
        """

        share_name = CleanHelpers.clean_name(self.cleaned_data['name'])

        existing_share = SharedPdf.objects.filter(owner=self.owner, name=share_name).first()

        if existing_share and not existing_share.deleted:
            raise forms.ValidationError('A Share with this name already exists!')

        return share_name

    def clean_password(self) -> str:  # pragma: no cover
        """Hash the user provided input."""

        return CleanHelpers.clean_password(self.cleaned_data['password'])

    def clean_expiration_input(self) -> str:  # pragma: no cover
        """Check if the expiration input is in the correct format _d_h_m, e.g. 1d0h22m."""

        return CleanHelpers.clean_time_input(self.cleaned_data['expiration_input'])

    def clean_deletion_input(self) -> str:  # pragma: no cover
        """Check if the deletion input is in the correct format _d_h_m, e.g. 1d0h22m."""

        return CleanHelpers.clean_time_input(self.cleaned_data['deletion_input'])

    def clean_max_views(self) -> int:  # pragma: no cover
        """Check that the provided max views are a positive integer"""

        return CleanHelpers.clean_max_views(self.cleaned_data['max_views'])


class SharedDescriptionForm(forms.ModelForm):
    """Form for changing the description of a shared PDF."""

    class Meta:
        model = SharedPdf
        fields = ['description']


class SharedNameForm(forms.ModelForm):
    """Form for changing the name of a shared PDF."""

    class Meta:
        model = SharedPdf
        fields = ['name']

    def clean_name(self) -> str:  # pragma: no cover
        """Clean the submitted pdf name. Removes trailing and multiple whitespaces."""
        pdf_name = CleanHelpers.clean_name(self.cleaned_data['name'])

        return pdf_name


class SharedMaxViewsForm(forms.ModelForm):
    """Form for changing the number of max views of a shared PDF."""

    class Meta:
        model = SharedPdf
        fields = ['max_views']

    def clean_max_views(self) -> int:  # pragma: no cover
        """Check that the provided max views are a positive integer"""

        return CleanHelpers.clean_max_views(self.cleaned_data['max_views'])


class SharedPasswordForm(forms.ModelForm):
    """Form for changing the password of a shared PDF."""

    class Meta:
        model = SharedPdf
        fields = ['password']

    def clean_password(self) -> str:  # pragma: no cover
        """Hash the user provided input."""

        return CleanHelpers.clean_password(self.cleaned_data['password'])


class SharedExpirationDateForm(forms.ModelForm):
    """Form for changing the tags of a PDF."""

    expiration_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1d0h22m'}),
    )

    class Meta:
        model = SharedPdf
        fields = []


class SharedDeletionDateForm(forms.ModelForm):
    """Form for changing the tags of a PDF."""

    deletion_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1d0h22m'}),
    )

    class Meta:
        model = SharedPdf
        fields = []


class ViewSharedPasswordForm(forms.Form):
    """Form for changing the description of a shared PDF."""

    password_input = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
    )

    def __init__(self, *args, **kwargs):
        """
        Adds the owner profile to the form. This is done, so we can check if the owner already has
        a PDF with the provided name in clean_name.
        """

        self.shared_pdf = kwargs.pop('shared_pdf', None)

        super(ViewSharedPasswordForm, self).__init__(*args, **kwargs)

    def clean_password_input(self):
        password = self.cleaned_data['password_input']

        if not check_password(password, self.shared_pdf.password):
            raise forms.ValidationError('Incorrect Password!')

        return password


class TagNameForm(forms.ModelForm):
    """Form for changing the name of a tag."""

    class Meta:
        model = Tag
        fields = ['name']

    def clean_name(self):
        # if not self.cleaned_data['name']:
        #     raise ValidationError('Please use a valid tag name!')

        return self.cleaned_data['name']


class CleanHelpers:
    @staticmethod
    def clean_file(file: File) -> File:
        """Clean the submitted pdf file. Checks if the file is a pdf."""

        # recommended to use at least the first 2048 bytes, as less can produce incorrect identification
        file_type = magic.from_buffer(file.read(2048), mime=True)

        if file_type.lower() != 'application/pdf':
            raise forms.ValidationError('Uploaded file is not a PDF!')

        return file

    @staticmethod
    def clean_name(pdf_name: str) -> str:
        """Clean the submitted pdf name. Removes trailing and multiple whitespaces."""

        pdf_name.strip()
        pdf_name = ' '.join(pdf_name.split())

        return pdf_name

    @staticmethod
    def clean_password(password: str) -> str:
        """Hash the password"""

        if password:
            password = make_password(password, salt='pdfding')

        return password

    @staticmethod
    def clean_max_views(max_views: int) -> int:
        """Check that the provided max views are a positive integer"""

        if max_views and not re.match(r'^[0-9]*$', str(max_views)):
            raise forms.ValidationError('Only positive numbers are allowed!')

        return max_views

    @staticmethod
    def clean_time_input(time_input: str) -> str:
        """Check if the provided time input is in the correct format _d_h_m, e.g. 1d0h22m."""

        if time_input and not re.match(r'^[0-9]+d[0-9]+h[0-9]+m$', str(time_input)):
            raise forms.ValidationError('Wrong format! Format needs to be _d_h_m!')

        return time_input
