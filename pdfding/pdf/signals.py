from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from pdf.models.pdf_models import Pdf
from pdf.services.workspace_services import create_personal_workspace


@receiver(post_save, sender=User)
def create_workspace(sender, instance, created, **kwargs):
    """Create the personal workspace when a user is created."""

    user = instance

    # Add personal workspace, workspace user and default collection when user is created
    if created:
        create_personal_workspace(user)


@receiver(pre_delete, sender=User)
def handle_workspaces_after_user_delete(sender, instance, **kwargs):
    """Deletes a workspace when a user is deleted if this user is the only owner."""

    user = instance
    workspaces = user.profile.workspaces

    for workspace in workspaces:
        if workspace.owners.count() == 1:
            workspace.delete()


@receiver(pre_delete, sender=Pdf)
def delete_orphan_tag(sender, instance, **kwargs):
    """
    Makes sure that there are no orphaned tags. If a tag is only used in a pdf object that is deleted, the tag will
    be deleted as well.
    """

    pdf = instance

    for tag in pdf.tags.all():
        # if only one pdf is  associated with the tag it is the one being deleted
        # in that case the tag should be deleted
        if tag.pdf_set.count() == 1:
            tag.delete()
