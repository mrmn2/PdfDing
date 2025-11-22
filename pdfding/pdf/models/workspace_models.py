from uuid import uuid4

from django.contrib.auth.models import User
from django.db import models


def get_uuid4_str() -> str:
    return str(uuid4())


class WorkspaceError(Exception):
    """Exceptions for workspace related problems"""


class WorkspaceRoles(models.TextChoices):
    OWNER = 'Owner'
    ADMIN = 'Admin'
    MEMBER = 'Member'
    GUEST = 'Guest'


class Workspace(models.Model):
    """The workspace model. Workspaces are the top level hierarchy."""

    id = models.CharField(primary_key=True, default=get_uuid4_str, max_length=36, editable=False, blank=False)
    name = models.CharField(max_length=50, blank=False)
    personal_workspace = models.BooleanField(blank=False, editable=False)

    def __str__(self):  # pragma: no cover
        return str(self.name)

    @property
    def users(self) -> models.QuerySet[User]:
        """Get the users of the workspace."""

        return User.objects.filter(workspaceuser__in=self.workspaceuser_set.all())

    @property
    def owners(self) -> models.QuerySet[User]:
        """Get the owners of the workspace."""

        owners = self.workspaceuser_set.filter(role=WorkspaceRoles.OWNER)
        owner_users = User.objects.filter(workspaceuser__in=owners)

        return owner_users

    @property
    def admins(self) -> models.QuerySet[User]:
        """Get the admins of the workspace."""

        admins = self.workspaceuser_set.filter(role=WorkspaceRoles.ADMIN)
        admin_users = User.objects.filter(workspaceuser__in=admins)

        return admin_users

    @property
    def members(self) -> models.QuerySet[User]:
        """Get the members of the workspace."""

        members = self.workspaceuser_set.filter(role=WorkspaceRoles.MEMBER)
        member_users = User.objects.filter(workspaceuser__in=members)

        return member_users

    @property
    def guests(self) -> models.QuerySet[User]:
        """Get the guests of the workspace."""

        guests = self.workspaceuser_set.filter(role=WorkspaceRoles.GUEST)
        guest_users = User.objects.filter(workspaceuser__in=guests)

        return guest_users

    @property
    def collections(self) -> models.QuerySet:
        """Get the collections of the workspace."""

        return self.collection_set.all()

    def add_user_to_workspace(self, user: User, role: WorkspaceRoles) -> None:
        """Add a user to the workspace."""

        if self.personal_workspace:
            raise WorkspaceError('Cannot add other users to personal workspaces!')
        elif user in self.users:
            raise WorkspaceError('User is already a user of the workspace!')
        else:
            WorkspaceUser.objects.create(workspace=self, user=user, role=role)


class WorkspaceUser(models.Model):
    """
    The workspace user model. It is linked to both a workspace and a user profile.
    Workspace users can have the roles owner, admin, member and guest.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False, blank=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    role = models.CharField(choices=WorkspaceRoles.choices, max_length=6, blank=False)
