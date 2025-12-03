from uuid import uuid4

from django.db import models
from pdf.models.workspace_models import Workspace


class Tag(models.Model):
    """The model for the tags used for organizing PDF files."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, blank=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, blank=False)

    def __str__(self):  # pragma: no cover
        return str(self.name)

    @staticmethod
    def parse_tag_string(tag_string: str) -> list[str]:
        if not tag_string:
            return []

        for forbidden_char in ['#', '&', '+']:
            tag_string = tag_string.replace(forbidden_char, '')

        names = tag_string.strip().split(' ')
        # remove empty names, sanitize remaining names
        names = [name.strip() for name in names if name]
        # remove duplicates
        names = [name.lower() for name in set(names)]

        return sorted(names)
