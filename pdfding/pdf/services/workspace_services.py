from django.contrib.auth.models import User
from pdf.models.collection_models import Collection
from pdf.models.workspace_models import Workspace, WorkspaceRoles, WorkspaceUser


def create_personal_workspace(creator: User) -> Workspace:
    """Create a personal workspace for a user including the workspace user and the default collection"""

    personal_workspace = Workspace.objects.create(id=str(creator.id), name='Personal', personal_workspace=True)
    WorkspaceUser.objects.create(workspace=personal_workspace, user=creator, role=WorkspaceRoles.OWNER)
    Collection.objects.create(id=str(creator.id), name='Default', workspace=personal_workspace, default_collection=True)

    return personal_workspace


def create_workspace(name: str, creator: User) -> Workspace:
    """Create a non personal workspace for a user including the workspace user and the default collection"""

    workspace = Workspace.objects.create(name=name, personal_workspace=False)
    WorkspaceUser.objects.create(workspace=workspace, user=creator, role=WorkspaceRoles.OWNER)
    Collection.objects.create(id=workspace.id, name='Default', workspace=workspace, default_collection=True)

    return workspace
