from base import base_views
from django.http import HttpRequest
from pdf.forms import CollectionForm
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


class Create(CreateCollectionMixin, base_views.BaseAdd):
    """View for creating new collections."""
