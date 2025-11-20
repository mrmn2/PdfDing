from uuid import uuid4

from django.contrib.auth.models import User
from django.db import models


def get_uuid4_str() -> str:
    return str(uuid4())


class Workspace(models.Model):
    """The workspace model. Workspaces are the top level hierarchy."""

    id = models.CharField(primary_key=True, default=get_uuid4_str, max_length=36, editable=False, blank=False)
    name = models.CharField(max_length=50, blank=False)
    personal_workspace = models.BooleanField(blank=False, editable=False)

    def __str__(self):  # pragma: no cover
        return str(self.name)


class WorkspaceRoles(models.TextChoices):
    OWNER = 'Owner'
    ADMIN = 'List'
    MEMBER = 'Member'
    GUEST = 'Guest'


class WorkspaceUser(models.Model):
    """
    The workspace user model. It is linked to both a workspace and a user profile.
    Workspace users can have the roles owner, admin, member and guest.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False, blank=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False)
    role = models.CharField(choices=WorkspaceRoles.choices, max_length=6, blank=False)
