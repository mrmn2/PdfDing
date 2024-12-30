import logging
from pathlib import Path

from backup.service import decrypt_file, get_encryption_key
from django.conf import settings
from django.core.management.base import BaseCommand
from minio import Minio

minio_client = Minio(
    endpoint=settings.BACKUP_ENDPOINT,
    secure=settings.BACKUP_SECURE,
    access_key=settings.BACKUP_ACCESS_KEY,
    secret_key=settings.BACKUP_SECRET_KEY,
)

logger = logging.getLogger('management')


class Command(BaseCommand):
    help = "Recover data from S3 backup"

    def handle(self, *args, **kwargs):
        logger.info('----------------------------------------------------')
        logger.info('Are you sure you want to proceed with the data recovery?')
        logger.info('If you are using a sqlite DB, this operation will overwrite your local DB!')
        logger.info('Type "y" to confirm')
        user_input = input()

        if user_input == 'y':
            logger.info('')
            logger.info('Starting data recovery')

            # get the encryption key. if backup encryption is disabled, result will be None
            encryption_key = get_encryption_key(
                settings.BACKUP_ENCRYPTION_ENABLED, settings.BACKUP_ENCRYPTION_PASSWORD, settings.BACKUP_ENCRYPTION_SALT
            )

            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
                logger.info('Recovering database')

                db_backup_path = settings.DATABASES['default']['BACKUP_NAME']

                self.get_file_from_minio(
                    db_backup_path.name,
                    db_backup_path.parent,
                    encryption_key,
                )

                db_backup_path.rename(settings.DATABASES['default']['NAME'])

            logger.info('Recovering PDF files and QR codes')
            objects = minio_client.list_objects(settings.BACKUP_BUCKET_NAME, recursive=True)
            for obj in objects:
                obj_name = obj.object_name
                if obj_name != settings.DATABASES['default']['BACKUP_NAME'].name:
                    self.get_file_from_minio(obj_name, settings.MEDIA_ROOT, encryption_key)

            logger.info('Data recovery completed successfully.')
            logger.info('----------------------------------------------------')
        else:  # pragma: no cover
            logger.info('Aborting data recovery.')
            logger.info('----------------------------------------------------')

    @staticmethod
    def get_file_from_minio(obj_name: str, target_parent_path: Path, encryption_key: bytes):
        """
        Get a file to minio. If an encryption key is provided the file will be decrypted beforehand using cryptography's
        fernet algorithm.
        """

        if encryption_key:
            # get encrypted file from minio, decrypt it and delete the local tmp file
            encrypted_file_path = Path(__file__).parent / 'tmp_encrypted'
            minio_client.fget_object(settings.BACKUP_BUCKET_NAME, obj_name, str(encrypted_file_path))
            decrypt_file(encryption_key, encrypted_file_path, target_parent_path / obj_name)
            encrypted_file_path.unlink()
        else:
            minio_client.fget_object(settings.BACKUP_BUCKET_NAME, obj_name, str(target_parent_path / obj_name))
