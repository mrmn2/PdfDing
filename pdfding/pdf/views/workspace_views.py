from base import base_views
from django.http import HttpRequest
from pdf.forms import WorkspaceForm
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


class Create(CreateWorkspaceMixin, base_views.BaseAdd):
    """View for creating new workspaces."""
