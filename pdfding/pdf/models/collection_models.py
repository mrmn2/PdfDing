from uuid import uuid4

from django.db import models
from pdf.models.workspace_models import Workspace


def get_uuid4_str() -> str:
    return str(uuid4())


class Collection(models.Model):
    """The model for the collections used for organizing PDF files."""

    id = models.CharField(primary_key=True, default=get_uuid4_str, max_length=36, editable=False, blank=False)
    name = models.CharField(max_length=50, blank=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, blank=False)
    default_collection = models.BooleanField(blank=False, editable=False)

    def __str__(self):  # pragma: no cover
        return str(self.name)
