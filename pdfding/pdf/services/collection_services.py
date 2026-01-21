from shutil import move

from core.settings import MEDIA_ROOT
from pdf.models.collection_models import Collection
from pdf.models.pdf_models import Pdf


def move_collection(collection: Collection) -> None:
    """
    Change the name of a collection and rename the collection directory on file system
    accordingly. Also handle all PDFs and shared PDFs.
    """

    # The new name is already set to the collection object by the form but not saved yet.
    new_collection_name = collection.name.lower()
    old_collection_name = Collection.objects.get(id=collection.id).name.lower()

    # move all files
    old_collection_path = MEDIA_ROOT / collection.workspace.id / old_collection_name
    new_collection_path = MEDIA_ROOT / collection.workspace.id / new_collection_name
    move(old_collection_path, new_collection_path)

    # adjust the file paths of the pdf and shared pdf objects
    for pdf in collection.pdfs:
        adjust_pdf_path(pdf, f'/{old_collection_name}/', f'/{new_collection_name}/')

    collection.save()


def adjust_pdf_path(pdf: Pdf, to_be_replaced: str, replace_with: str, move_files: bool = False) -> None:
    """Adjust path of PDF and its shared PDFs when the path of a collection is changed"""

    old_pdf_file_name = pdf.file.name
    new_pdf_file_name = old_pdf_file_name.replace(to_be_replaced, replace_with, 1)
    old_preview_file_name = pdf.preview.name
    new_preview_file_name = old_preview_file_name.replace(to_be_replaced, replace_with, 1)
    old_thumbnail_file_name = pdf.thumbnail.name
    new_thumbnail_file_name = old_thumbnail_file_name.replace(to_be_replaced, replace_with, 1)

    if move_files:
        for old, new in zip(
            [old_pdf_file_name, old_preview_file_name, old_thumbnail_file_name],
            [new_pdf_file_name, new_preview_file_name, new_thumbnail_file_name],
        ):
            move_collection_file(old, new)

    pdf.file.name = new_pdf_file_name
    pdf.preview.name = new_preview_file_name
    pdf.thumbnail.name = new_thumbnail_file_name

    pdf.save()

    for shared_pdf in pdf.sharedpdf_set.all():
        old_qr_file_name = shared_pdf.file.name
        new_qr_file_name = old_qr_file_name.replace(to_be_replaced, replace_with, 1)

        if move_files:
            move_collection_file(old_qr_file_name, new_qr_file_name)

        shared_pdf.file.name = new_qr_file_name
        shared_pdf.save()


def move_collection_file(old_file_name: str, new_file_name: str) -> None:
    """Move the file of collection, e.g. the file belonging to a pdf."""

    old_path = MEDIA_ROOT / old_file_name
    new_path = MEDIA_ROOT / new_file_name

    # make sure parent dir exists
    new_path.parent.mkdir(exist_ok=True, parents=True)

    old_path.rename(new_path)
