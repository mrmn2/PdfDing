from base import base_views
from django.http import HttpRequest
from pdf.forms import WorkspaceDescriptionForm, WorkspaceForm, WorkspaceNameForm
from pdf.models.workspace_models import Workspace
from pdf.services.workspace_services import create_workspace


class BaseWorkspaceMixin:
    obj_name = 'workspace'


class CreateWorkspaceMixin(BaseWorkspaceMixin):
    form = WorkspaceForm
    template_name = 'create_workspace.html'

    def get_context_get(self, request: HttpRequest, __):
        """Get the context needed to be passed to the template containing the form for creating a workspace."""

        form = self.form

        context = {'form': form(profile=request.user.profile)}

        return context

    @classmethod
    def obj_save(cls, form: WorkspaceForm, request: HttpRequest, _):
        """Save the workspace based on the submitted form."""

        created_ws = create_workspace(
            name=form.data['name'], description=form.data['description'], creator=request.user
        )

        profile = request.user.profile
        profile.current_workspace_id = created_ws.id
        profile.save()


class WorkspaceMixin(BaseWorkspaceMixin):
    @staticmethod
    def get_object(request: HttpRequest, ws_id: str) -> Workspace:
        """Get the current workspace."""

        user_profile = request.user.profile
        ws = user_profile.workspaces.get(id=ws_id)

        return ws


class EditWorkspaceMixin(WorkspaceMixin):
    fields_requiring_extra_processing = []

    @staticmethod
    def get_edit_form_dict():
        """Get the forms of the fields that can be edited as a dict."""

        form_dict = {
            'description': WorkspaceDescriptionForm,
            'name': WorkspaceNameForm,
        }

        return form_dict

    def get_edit_form_get(self, field_name: str, workspace: Workspace):
        """Get the form belonging to the specified field."""

        form_dict = self.get_edit_form_dict()

        initial_dict = {
            'name': {'name': workspace.name},
            'description': {'description': workspace.description},
        }

        form = form_dict[field_name](initial=initial_dict[field_name])

        return form


class Create(CreateWorkspaceMixin, base_views.BaseAdd):
    """View for creating new workspaces."""


class Details(WorkspaceMixin, base_views.BaseDetails):
    """View for displaying the details page of a workspace."""


class Edit(EditWorkspaceMixin, base_views.BaseDetailsEdit):
    """
    The view for editing a workspace's name and description. The field, that is to be changed, is specified by the
    'field' argument.
    """
