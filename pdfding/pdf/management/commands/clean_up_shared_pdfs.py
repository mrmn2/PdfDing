import logging

from django.core.management.base import BaseCommand
from pdf.models import SharedPdf

logger = logging.getLogger('management')


class Command(BaseCommand):
    help = "Clean up shared PDFs with a deletion date in the past."

    def handle(self, *args, **kwargs):
        logger.info('Cleaning up shared PDFs with a deletion date in the past.')

        shared_pdfs = SharedPdf.objects.all()

        for shared_pdf in shared_pdfs:
            if shared_pdf.deleted:
                shared_pdf.delete()
