from django.db.models.signals import pre_delete
from django.dispatch import receiver
from pdf.models.pdf_models import Pdf


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
