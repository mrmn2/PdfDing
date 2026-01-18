from base import base_views
from django.contrib import messages
from django.http import HttpRequest
from pdf.forms import CollectionDescriptionForm, CollectionForm, CollectionNameForm
from pdf.models.collection_models import Collection
from pdf.services.collection_services import move_collection
from pdf.services.pdf_services import check_object_access_allowed
from pdf.services.workspace_services import create_collection


class BaseCollectionMixin:
    obj_name = 'collection'


class CreateCollectionMixin(BaseCollectionMixin):
    form = CollectionForm
    template_name = 'create_collection.html'

    def get_context_get(self, request: HttpRequest, __):
        """Get the context needed to be passed to the template containing the form for creating a collection."""

        form = self.form

        context = {'form': form(profile=request.user.profile)}

        return context

    @classmethod
    def obj_save(cls, form: CollectionForm, request: HttpRequest, _):
        """Save the collection based on the submitted form."""

        workspace = request.user.profile.current_workspace

        create_collection(workspace=workspace, collection_name=form.data['name'], description=form.data['description'])


class CollectionMixin(BaseCollectionMixin):
    @staticmethod
    @check_object_access_allowed
    def get_object(request: HttpRequest, collection_id: str) -> Collection:
        """Get the current collection."""

        user_profile = request.user.profile
        collection = user_profile.collections.get(id=collection_id)

        return collection


class EditCollectionMixin(CollectionMixin):
    fields_requiring_extra_processing = ['name']

    @staticmethod
    def get_edit_form_dict():
        """Get the forms of the fields that can be edited as a dict."""

        form_dict = {
            'description': CollectionDescriptionForm,
            'name': CollectionNameForm,
        }

        return form_dict

    def get_edit_form_get(self, field_name: str, collection: Collection):
        """Get the form belonging to the specified field."""

        form_dict = self.get_edit_form_dict()

        initial_dict = {
            'name': {'name': collection.name},
            'description': {'description': collection.description},
        }

        form = form_dict[field_name](initial=initial_dict[field_name])

        return form

    @classmethod
    def process_field(cls, field_name: str, collection: Collection, request: HttpRequest, form_data: dict):
        """Process fields that are not covered in the base edit view."""

        if field_name == 'name':
            profile = request.user.profile
            existing_collection = profile.collections.filter(name__iexact=form_data.get('name').strip()).first()

            if existing_collection and str(existing_collection.id) != str(collection.id):
                messages.warning(request, 'This name is already used by another collection in this workspace!')
            else:
                move_collection(collection)


class Create(CreateCollectionMixin, base_views.BaseAdd):
    """View for creating new collections."""


class Edit(EditCollectionMixin, base_views.BaseDetailsEdit):
    """
    The view for editing a collection's name and description. The field, that is to be changed, is specified by the
    'field' argument.
    """
