import re

import magic
import requests
from django import forms
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from pdf.models.pdf_models import Pdf
from pdf.models.shared_pdf_models import SharedPdf
from pdf.services.workspace_services import check_if_pdf_with_name_exists, get_shared_pdfs_of_workspace


class AddFormNoFile(forms.ModelForm):
    """Class for creating the form for adding PDFs in the demo mode."""

    tag_string = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add Tags'}),
        help_text='Optional, enter any number of tags separated by space and without the hashtag (#). '
        'If a tag does not exist it will be automatically created.',
    )

    use_file_name = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Pdf
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Add PDF Name'}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Add Description'}),
            'notes': forms.Textarea(attrs={'rows': 8, 'placeholder': 'Add Notes'}),
            'file_directory': forms.TextInput(attrs={'placeholder': 'Add File Directory'}),
        }

        fields = ['name', 'description', 'notes', 'file_directory']

    def __init__(self, *args, **kwargs):
        """
        Adds the profile to the form. This is done, so we can access information about the profile
        when creating a new pdf.
        """

        self.profile = kwargs.pop('profile', None)
        if not self.profile:
            raise KeyError('profile')

        collections = self.profile.collections

        super(AddFormNoFile, self).__init__(*args, **kwargs)
        self.fields['collection'] = forms.ChoiceField(
            choices=[(collection.id, collection.name) for collection in collections],
        )

    def clean_name(self) -> str:
        """
        Clean the submitted pdf name. Removes trailing and multiple whitespaces. Also checks if the user already
        has an uploaded PDF with the same name.
        """

        pdf_name = CleanHelpers.clean_name(self.cleaned_data['name'])

        current_workspace = self.profile.current_workspace
        existing_pdf = check_if_pdf_with_name_exists(pdf_name, current_workspace)

        # only raise validation error if name is not the dummy placeholder from the frontend
        # otherwise it will be replaced by the filename in "clean".
        if pdf_name != 'bb36974a-3792-47c5-96cc-c79adb87cf82' and existing_pdf:
            raise forms.ValidationError('A PDF with this name already exists!')

        return pdf_name

    def clean_tag_string(self) -> str:  # pragma: no cover
        return CleanHelpers.clean_tag_string_file_directory(self.cleaned_data['tag_string'])

    def clean_file_directory(self) -> str:  # pragma: no cover
        return CleanHelpers.clean_file_directory(self.cleaned_data['file_directory'])


class AddForm(AddFormNoFile):
    """Class for creating the form for adding PDFs."""

    url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Add URL'}),
        help_text='Optional, enter a URL to a PDF file.',
    )

    class Meta(AddFormNoFile.Meta):
        model = Pdf
        widgets = AddFormNoFile.Meta.widgets
        widgets['file'] = forms.ClearableFileInput(attrs={'accept': 'application/pdf'})

        fields = AddFormNoFile.Meta.fields
        fields.append('file')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        url = cleaned_data.get('url')

        if not file and not url:  # pragma: no cover
            raise forms.ValidationError('Either a file or a URL must be provided.')

        if file and url:   # pragma: no cover
            raise forms.ValidationError('Provide either a file or a URL, not both.')

        if url:   # pragma: no cover
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                cleaned_data['file'] = ContentFile(response.content, name=cleaned_data.get('name'))
            except requests.exceptions.RequestException as e:
                raise forms.ValidationError(f'Error downloading PDF: {e}')

        return cleaned_data

    def clean_file(self) -> File:  # pragma: no cover
        """Clean the submitted pdf file. Checks if the file is a pdf."""
        if self.cleaned_data.get('file'):
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


class BulkAddFormNoFile(forms.Form):
    """Class for creating the form for bulk adding PDFs in the demo mode."""

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add Description'}),
        help_text='Optional',
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 8, 'placeholder': 'Add Notes'}),
        help_text='Optional, supports Markdown',
    )

    tag_string = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add Tags'}),
        help_text='Optional, enter any number of tags separated by space and without the hashtag (#). '
        'If a tag does not exist it will be automatically created.',
    )

    file_directory = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add File Directory'}),
        help_text='Optional, save file in a sub directory of the pdf directory, e.g: important/pdfs',
    )

    def __init__(self, *args, **kwargs):
        """
        Adds the profile to the form. This is done, so we can access information about the profile
        when creating a new pdf.
        """

        self.profile = kwargs.pop('profile', None)
        if not self.profile:
            raise KeyError('profile')

        collections = self.profile.collections

        super(BulkAddFormNoFile, self).__init__(*args, **kwargs)
        self.fields['collection'] = forms.ChoiceField(
            choices=[(collection.id, collection.name) for collection in collections],
        )

    def clean_file(self):
        for file in self.cleaned_data['file']:
            CleanHelpers.clean_file(file)

    def clean_tag_string(self) -> str:  # pragma: no cover
        return CleanHelpers.clean_tag_string_file_directory(self.cleaned_data['tag_string'])

    def clean_file_directory(self) -> str:  # pragma: no cover
        return CleanHelpers.clean_file_directory(self.cleaned_data['file_directory'])


class BulkAddForm(BulkAddFormNoFile):
    """Class for creating the form for bulk adding PDFs."""

    file = MultipleFileField(
        required=True,
        widget=MultipleFileInput(attrs={'accept': 'application/pdf'}),
    )


class DescriptionForm(forms.ModelForm):
    """Form for changing the description of a PDF."""

    class Meta:
        model = Pdf
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}
        fields = ['description']


class NotesForm(forms.ModelForm):
    """Form for changing the notes of a PDF."""

    class Meta:
        model = Pdf
        widgets = {'notes': forms.Textarea(attrs={'rows': 20})}
        fields = ['notes']


class NameForm(forms.ModelForm):
    """Form for changing the name of a PDF."""

    class Meta:
        model = Pdf
        fields = ['name']

    def clean_name(self) -> str:  # pragma: no cover
        """Clean the submitted pdf name. Removes trailing and multiple whitespaces."""

        pdf_name = CleanHelpers.clean_name(self.cleaned_data['name'])

        return pdf_name


class FileDirectoryForm(forms.ModelForm):
    """Form for changing the directory of a PDF."""

    class Meta:
        model = Pdf
        fields = ['file_directory']

    def clean_file_directory(self) -> str:  # pragma: no cover
        """Clean the submitted pdf file directory name."""

        file_directory = self.cleaned_data['file_directory']

        return CleanHelpers.clean_file_directory(file_directory)


class PdfTagsForm(forms.ModelForm):
    """Form for changing the tags of a PDF."""

    tag_string = forms.CharField(widget=forms.TextInput(), required=False)

    class Meta:
        model = Pdf
        fields = []

    def clean_tag_string(self) -> str:  # pragma: no cover
        return CleanHelpers.clean_tag_string_file_directory(self.cleaned_data['tag_string'])


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
        Adds the profile to the form. This is done, so we can access information about the profile
        when creating a new shared pdf.
        """

        self.profile = kwargs.pop('profile', None)
        if not self.profile:
            raise KeyError('profile')

        super(ShareForm, self).__init__(*args, **kwargs)

    def clean_name(self) -> str:
        """
        Clean the submitted share name. Removes trailing and multiple whitespaces. Also checks if the user already
        has a share with the same name.
        """

        share_name = CleanHelpers.clean_name(self.cleaned_data['name'])

        shared_pdfs = get_shared_pdfs_of_workspace(self.profile.current_workspace)
        existing_share = shared_pdfs.filter(name__iexact=share_name).first()

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
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}
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
        help_text='This PDF is password protected',
    )

    def __init__(self, *args, **kwargs):
        """Adds the shared pdf to the form."""

        self.shared_pdf = kwargs.pop('shared_pdf', None)

        super(ViewSharedPasswordForm, self).__init__(*args, **kwargs)

    def clean_password_input(self):
        password = self.cleaned_data['password_input']

        if not check_password(password, self.shared_pdf.password):
            raise forms.ValidationError('Incorrect Password!')

        return password


class TagNameForm(forms.Form):
    """Form for changing the name of a tag."""

    name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    def clean_name(self) -> str:
        new_tag_name = self.cleaned_data['name'].strip()

        if re.search(r'\s', new_tag_name):
            raise ValidationError('Tag names are not allowed to contain spaces!')

        new_tag_name = CleanHelpers.clean_tag_string_file_directory(new_tag_name)

        return new_tag_name


class WorkspaceForm(forms.Form):
    """Class for creating the form for creating workspaces."""

    name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add Workspace Name'}),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Add a workspace description'}),
        help_text='Optional',
    )

    def __init__(self, *args, **kwargs):
        """
        Adds the profile to the form. This is done, so we can access information about the profile
        when creating a new workspace.
        """

        self.profile = kwargs.pop('profile', None)
        if not self.profile:
            raise KeyError('profile')

        super(WorkspaceForm, self).__init__(*args, **kwargs)

    def clean_name(self) -> str:
        """
        Clean the submitted workspace name. Removes trailing and multiple whitespaces. Checks that only
        numbers, letters, '_' and '-' are used.
        """

        ws_name = CleanHelpers.clean_name(self.cleaned_data['name'])

        if ws_name in ['_', '-']:
            raise forms.ValidationError('"_" or "-" are not valid workspace names!')
        elif ws_name and not re.match(r'^[A-Za-z0-9-_]*$', ws_name):
            raise forms.ValidationError('Only "-", "_", numbers or letters are allowed!')
        if len(ws_name) > 50:
            raise forms.ValidationError('Maximum number of characters for a workspace name is 50!')

        return ws_name


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
    def clean_name(name: str) -> str:
        """Clean the submitted name. Removes trailing and multiple whitespaces."""

        name.strip()
        name = ' '.join(name.split())

        return name

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

    @classmethod
    def clean_file_directory(cls, file_directory: str) -> str:  # pragma: no cover
        """
        Clean the submitted file directory. Removes trailing, multiple whitespaces. Raises ValidationError for not
        allowed chars. Allowed are only alphanumeric chars and those in ['/', '-', '_', space].
        """

        if file_directory:
            file_directory = file_directory.strip()

            if re.search(r'\s', file_directory):
                raise ValidationError('Directories are not allowed to contain spaces!')

            file_directory = cls.clean_tag_string_file_directory(file_directory)

        return file_directory

    @staticmethod
    def clean_tag_string_file_directory(input_string: str):
        """
        Clean the input string. Allowed are only alphanumeric chars and those in ['/', '-', '_', space].
        """

        if input_string:
            for char in input_string:
                if not (char.isalnum() or char in ['/', '-', '_', ' ']):
                    raise forms.ValidationError('Only letters, numbers, "/", "-" and "_" are valid characters!')

            string_split = input_string.split(' ')

            for string_part in string_split:
                # only process non-empty strings
                # if a string has multiple spaces between this would cause a IndexError otherwise.
                if string_part:
                    string_part = string_part.strip()

                    if string_part[0] == '/' or string_part[-1] == '/':
                        raise forms.ValidationError('Not allowed to begin or end with "/"!')

                    if re.search(r'/{2,}', string_part):
                        raise forms.ValidationError('Not allowed to contain consecutive "/" characters!')

        return input_string
