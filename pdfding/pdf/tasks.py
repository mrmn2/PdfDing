import logging
import traceback
from pathlib import Path

import magic
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from huey import crontab
from huey.contrib.djhuey import periodic_task
from pdf import service
from pdf.models import Pdf, Tag

logger = logging.getLogger('huey')


@periodic_task(crontab(minute='*/5'), retries=0)
def consume_task():  # pragma: no cover
    """
    Periodic huey task for creating pdf instances from pdf files put into the consume folder.
    """

    if settings.CONSUME_ENABLED:
        consume_function(settings.CONSUME_SKIP_EXISTING)


def consume_function(skip_existing: bool):
    """Create pdf instances for pdf files present in the consume folder."""

    if not settings.CONSUME_DIR.exists():  # pragma: no cover
        settings.CONSUME_DIR.mkdir(exist_ok=True)

    user_consume_paths = [path for path in settings.CONSUME_DIR.iterdir() if path.is_dir()]
    tag_names = Tag.parse_tag_string(settings.CONSUME_TAG_STRING)

    for user_consume_path in user_consume_paths:
        user = User.objects.get(id=user_consume_path.name)
        tags = service.process_tag_names(tag_names, user.profile)
        user_consume_file_paths = [path for path in user_consume_path.iterdir() if path.is_file()]

        if skip_existing:
            pdf_info_list = service.get_pdf_info_list(user.profile)
        else:
            pdf_info_list = []

        for file_path in user_consume_file_paths:
            try:
                if passes_consume_condition(file_path, skip_existing, pdf_info_list):
                    pdf_name = service.create_unique_name_from_file(file_path, user.profile)

                    with file_path.open(mode="rb") as f:
                        pdf_file = File(f, name=file_path.name)
                        pdf = Pdf.objects.create(owner=user.profile, name=pdf_name, file=pdf_file)

                    pdf.tags.set(tags)
                    service.set_number_of_pages(pdf)

            except Exception as e:  # pragma: no cover # nosec # noqa
                logger.info(f'Could not create pdf from "{file_path.name}" of user "{user.id}"')
                logger.info(traceback.format_exc())

            file_path.unlink()


def passes_consume_condition(file_path: Path, skip_existing: bool, pdf_info_list: list[tuple]):
    """
    Check if the file is a pdf file. If existing files should be skipped also checks if a pdf with the same name and
    file size does already exist.
    """

    file_type = magic.from_file(file_path, mime=True).lower()

    return file_type == 'application/pdf' and not (
        skip_existing and (service.create_name_from_file(file_path), file_path.stat().st_size) in pdf_info_list
    )
