from pathlib import Path

from core.settings import MEDIA_ROOT


def get_workspace_path(workspace) -> Path:  # pragma: no cover
    """Get the path of a workspace."""

    return MEDIA_ROOT / get_workspace_dir(workspace)


def get_collection_path(collection) -> Path:  # pragma: no cover
    """Get the path of a collection."""

    return MEDIA_ROOT / get_collection_dir(collection)


def get_workspace_dir(workspace) -> str:
    """Get the directory of a workspace."""

    return workspace.id


def get_collection_dir(collection) -> str:
    """Get the directory of a collection."""

    return f'{get_workspace_dir(collection.workspace)}/{collection.name.lower()}'
