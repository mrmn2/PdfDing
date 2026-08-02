from pathlib import Path
from unittest import mock

import pytest
from backup.management.commands.recover_data import Command
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.management import call_command
from django.test import TestCase


class TestRecoverData(
    TestCase,
):
    mock_object_1 = mock.Mock()
    mock_object_1.object_name = 'pdf_1.pdf'
    mock_object_2 = mock.Mock()
    mock_object_2.object_name = 'backup.sqlite3'

    mock_objects = [mock_object_1, mock_object_2]

    @mock.patch('backup.management.commands.recover_data.Minio.list_objects', return_value=mock_objects)
    @mock.patch('backup.management.commands.recover_data.Path.rename')
    @mock.patch('backup.management.commands.recover_data.Command.get_file_from_minio')
    @mock.patch('backup.management.commands.recover_data.get_encryption_key', return_value=b'key')
    @mock.patch('builtins.input', return_value='y')
    def test_recover_data(
        self, mock_input, mock_get_encryption_key, mock_get_file_from_minio, mock_rename, mock_list_objects
    ):
        call_command('recover_data')

        mock_get_encryption_key.assert_called_with(True, 'password', 'pdfding')
        mock_rename.assert_called_with(settings.DATABASES['default']['NAME'])

        self.assertEqual(mock_get_file_from_minio.call_count, 2)
        mock_get_file_from_minio.assert_has_calls(
            [
                mock.call('backup.sqlite3', Path(__file__).parents[2] / 'db', b'key'),
                mock.call('pdf_1.pdf', Path(__file__).parents[2] / 'media', b'key'),
            ],
        )

    @mock.patch('backup.management.commands.recover_data.Minio.fget_object')
    def test_get_file_from_minio_no_encryption(self, mock_fget_object):
        Command.get_file_from_minio('file_name', settings.MEDIA_ROOT, None)

        mock_fget_object.assert_called_with('pdfding', 'file_name', str(settings.MEDIA_ROOT / 'file_name'))

    @mock.patch('backup.tasks.Path.unlink')
    @mock.patch('backup.management.commands.recover_data.decrypt_file')
    @mock.patch('backup.management.commands.recover_data.Minio.fget_object')
    def test_get_file_from_minio_with_encryption(self, mock_fput_object, mock_decrypt_file, mock_unlink):
        Command.get_file_from_minio('file_name', settings.MEDIA_ROOT, b'key')

        tmp_file_path = Path(__file__).parents[1] / 'management' / 'commands' / 'tmp_encrypted'

        mock_fput_object.assert_called_with('pdfding', 'file_name', str(tmp_file_path))
        mock_decrypt_file.assert_called_with(b'key', tmp_file_path, settings.MEDIA_ROOT / 'file_name')
        mock_unlink.assert_called_with()

    def test_get_file_from_minio_exception(self):
        with pytest.raises(SuspiciousOperation):
            Command.get_file_from_minio('../file_name', settings.MEDIA_ROOT, None)
