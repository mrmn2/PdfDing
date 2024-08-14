import logging
import sqlite3
from pathlib import Path

from django.conf import settings
from huey import crontab
from huey.contrib.djhuey import periodic_task
from minio import Minio
from pdf.models import Pdf

logger = logging.getLogger('huey')
minio_client = Minio(
    endpoint=settings.BACKUP_ENDPOINT,
    secure=settings.BACKUP_SECURE,
    access_key=settings.BACKUP_ACCESS_KEY,
    secret_key=settings.BACKUP_SECRET_KEY,
)


def parse_cron_schedule(cron_schedule: str) -> dict[str, str]:
    """
    Parse a cron schedule so that it can be used as an input for a huey periodic tasc.

    Input: '3 */2 6 7 *'
    Result: {'minute': '3', 'hour': '*/2', 'day': '6', 'month': '7', 'day_of_week': '*'}
    """

    cron_schedule_split = cron_schedule.split()
    key_list = ['minute', 'hour', 'day', 'month', 'day_of_week']
    return_dict = {key: value for key, value in zip(key_list, cron_schedule_split)}

    return return_dict


@periodic_task(crontab(**parse_cron_schedule(settings.BACKUP_SCHEDULE)), retries=3, retry_delay=60)
def backup_task():  # pragma: no cover
    """
    Periodic huey task for backing up the PDF files and (if used) the sqlite database.
    """

    backup_function()


def backup_function():
    """
    Function for backing up the PDF files and (if used) the sqlite database. This is a separate function in order
    to make the unit tests easier.
    """

    logger.info('----------------------------------------------------')
    logger.info('Backup is being started')

    if not minio_client.bucket_exists(settings.BACKUP_BUCKET_NAME):
        logger.info('Bucket not existing -> creating bucket {settings.BACKUP_BUCKET_NAME}')
        minio_client.make_bucket(settings.BACKUP_BUCKET_NAME)

    # backup sqlite db
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
        logger.info('Backing up sqlite db')
        backup_path = settings.DATABASES['default']['BACKUP_NAME']
        backup_sqlite(settings.DATABASES['default']['NAME'], backup_path)
        minio_client.fput_object(settings.BACKUP_BUCKET_NAME, backup_path.name, backup_path)
        backup_path.unlink()

    # add new files to minio, delete deleted files from minio
    to_be_added, to_be_deleted = difference_local_minio()

    logger.info(f'Need to backup {len(to_be_added)} files.')
    logger.info(f'Need to remove {len(to_be_deleted)} files from backup.')

    for i, pdf_name in enumerate(to_be_added):
        minio_client.fput_object(settings.BACKUP_BUCKET_NAME, pdf_name, settings.MEDIA_ROOT / pdf_name)
        if (i + 1) % 10 == 0:
            logger.info(f'Added {i + 1} / {len(to_be_added)} files')

    for i, pdf_name in enumerate(to_be_deleted):
        minio_client.remove_object(settings.BACKUP_BUCKET_NAME, pdf_name)
        if (i + 1) % 10 == 0:
            logger.info(f'Removed {i + 1} / {len(to_be_deleted)} files')

    logger.info('Backup completed successfully.')
    logger.info('----------------------------------------------------')


def backup_sqlite(db_path: Path, backup_path: Path):
    """Create a backup of a sqlite database"""

    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES, uri=True)
    backup_conn = sqlite3.connect(backup_path, uri=True)
    with backup_conn:
        conn.backup(backup_conn)
    backup_conn.close()
    conn.close()


def difference_local_minio() -> tuple[set[str], set[str]]:
    """
    Compare the local PDF files to the PDF files in the minio bucket.

    Returns two sets: - one with the file names that need to be added to the minio bucket as they were recently uploaded
                        by users.
                    - and one with the names of the files that need to be removed from the bucket as they are no longer
                      present on the local system, e.g. a user has deleted a file.
    """

    set_of_local_files = {pdf.file.name for pdf in Pdf.objects.all()}
    set_of_minio_files = {
        object.object_name
        for object in minio_client.list_objects(settings.BACKUP_BUCKET_NAME, recursive=True)
        if object.object_name != settings.DATABASES['default']['BACKUP_NAME'].name
    }

    to_be_deleted = set_of_minio_files.difference(set_of_local_files)
    to_be_added = set_of_local_files.difference(set_of_minio_files)

    return to_be_added, to_be_deleted