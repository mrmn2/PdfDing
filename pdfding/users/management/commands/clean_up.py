import logging
from pathlib import Path
from shutil import copy

from django.conf import settings
from django.core.management.base import BaseCommand
from pdf.models.shared_pdf_models import SharedPdf

logger = logging.getLogger('management')


class Command(BaseCommand):
    help = "Clean up data on start up"

    def handle(self, *args, **kwargs):
        clean_up_deleted_shared_pdfs()

        if settings.DEMO_MODE:
            clean_demo_db()


def clean_up_deleted_shared_pdfs():
    """Delete shared PDFs with a deletion date in the past."""

    logger.info('Cleaning up shared PDFs with a deletion date in the past.')

    shared_pdfs = SharedPdf.objects.all()

    for shared_pdf in shared_pdfs:
        if shared_pdf.deleted:
            shared_pdf.delete()


def clean_demo_db(
    db_path: Path = settings.BASE_DIR / 'db' / 'db.sqlite3',
    after_migration_db_path: Path = settings.BASE_DIR / 'db' / 'migrated.sqlite3',
):
    """Clean the database for the demo mode. In this state the db will have applied migrations but no users or pdfs."""

    logger.info('Cleaning up the demo database.')

    # If the after_migration_db_path is not present, then the container is started for the first time.
    # This means only the migrations were applied until now, so we want preserve this state.
    if not after_migration_db_path.exists():
        copy(db_path, after_migration_db_path)
    # otherwise replace the migrations db.
    else:
        db_path.unlink()
        copy(after_migration_db_path, db_path)
