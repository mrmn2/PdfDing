from django.contrib.auth.models import User
from django.db.models import QuerySet
from pdf.models.collection_models import Collection
from pdf.models.pdf_models import Pdf
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


def create_collection(workspace: Workspace, collection_name: str) -> Collection:
    """Create a collection and add it to the workspace"""

    if workspace.collections.filter(name=collection_name).count():
        raise WorkspaceError(f'There is already a collection named {collection_name}!')
    else:
        return Collection.objects.create(workspace=workspace, name=collection_name, default_collection=False)


def get_pdfs_of_workspace(workspace: Workspace) -> QuerySet[Pdf]:
    """Get all PDFs of the workspace."""

    return Pdf.objects.filter(collection__in=workspace.collections)


def check_if_pdf_with_name_exists(name: str, workspace: Workspace) -> bool:
    """Check if a PDF with the specified name exists in the workspace."""

    if get_pdfs_of_workspace(workspace).filter(name=name).first():
        return True
    else:
        return False
