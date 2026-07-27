from django import template
from pdf.models.pdf_models import Pdf
from pdf.services.pdf_services import get_or_create_pdf_reading_info
from users.models import Profile

register = template.Library()


@register.simple_tag
def get_progress(pdf: Pdf, profile: Profile) -> float:
    """Get the progress of a user in a PDF."""

    current_page = get_current_page(pdf, profile)

    progress = round(100 * current_page / pdf.number_of_pages)

    return min(progress, 100)


@register.simple_tag
def get_current_page(pdf: Pdf, profile: Profile) -> int:
    """Get the current page of a user in a PDF."""

    pdf_reading_info = get_or_create_pdf_reading_info(pdf, profile)

    if pdf_reading_info.views == 0:
        current_page = 0
    else:
        current_page = pdf_reading_info.current_page

    return max(current_page, 0)
