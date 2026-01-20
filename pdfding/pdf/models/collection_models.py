from shutil import rmtree
from uuid import uuid4

from django.db import models
from pdf.models.helpers import get_collection_path
from pdf.models.workspace_models import Workspace


def get_uuid4_str() -> str:
    return str(uuid4())


class CollectionError(Exception):
    """Exceptions for collection related problems"""


class Collection(models.Model):
    """The model for the collections used for organizing PDF files."""

    id = models.CharField(primary_key=True, default=get_uuid4_str, max_length=36, editable=False, blank=False)
    creation_date = models.DateTimeField(blank=False, editable=False, auto_now_add=True)
    description = models.TextField(default='', blank=True)
    name = models.CharField(max_length=50, blank=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, blank=False)
    default_collection = models.BooleanField(blank=False, editable=False)

    def __str__(self):  # pragma: no cover
        return str(self.name)

    def delete(self, *args, **kwargs) -> None:
        """
        Override default delete method so that the collection directory gets deleted after the collection is deleted.
        """

        collection_path = get_collection_path(self)
        super().delete(*args, **kwargs)

        try:
            rmtree(collection_path)
        except Exception:  # pragma: no cover # nosec B110
            pass

    @property
    def pdfs(self) -> models.QuerySet:
        """Get the pdfs of the collection"""

        return self.pdf_set.all()
