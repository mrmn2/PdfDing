from django.contrib.auth.models import User
from pdf.models.collection_models import Collection
from pdf.models.workspace_models import Workspace, WorkspaceError, WorkspaceRoles, WorkspaceUser
from users.models import Profile


def create_personal_workspace(creator: User) -> Workspace:
    """Create a personal workspace for a user including the workspace user and the default collection"""

    if (
        Profile.objects.filter(user=creator).count()
        and creator.profile.workspaces.filter(personal_workspace=True).count() > 0
    ):
        raise WorkspaceError(f'There is already a personal workspace for user {creator.email}!')
    else:
        personal_workspace = Workspace.objects.create(id=str(creator.id), name='Personal', personal_workspace=True)
        WorkspaceUser.objects.create(workspace=personal_workspace, user=creator, role=WorkspaceRoles.OWNER)
        Collection.objects.create(
            id=str(creator.id), name='Default', workspace=personal_workspace, default_collection=True
        )

    return personal_workspace


def create_workspace(name: str, creator: User) -> Workspace:
    """Create a non personal workspace for a user including the workspace user and the default collection"""

    if creator.profile.workspaces.filter(name=name).count():
        raise WorkspaceError(f'There is already a workspace named {name}!')
    else:
        workspace = Workspace.objects.create(name=name, personal_workspace=False)
        WorkspaceUser.objects.create(workspace=workspace, user=creator, role=WorkspaceRoles.OWNER)
        Collection.objects.create(id=workspace.id, name='Default', workspace=workspace, default_collection=True)

    return workspace


def create_collection(workspace, collection_name) -> Collection:
    """Create a collection and add it to the workspace"""

    if workspace.collections.filter(name=collection_name).count():
        raise WorkspaceError(f'There is already a collection named {collection_name}!')
    else:
        return Collection.objects.create(workspace=workspace, name=collection_name, default_collection=False)
