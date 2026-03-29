from datetime import datetime, timedelta, timezone

from django.contrib.sessions.models import Session
from pdf.models.shared_pdf_models import SharedPdf


def check_shared_access_allowed_by_identifier(identifier: str, session: Session):
    """Check if access to shared pdf is allowed based on session."""

    shared_pdf = SharedPdf.objects.get(pk=identifier)

    return check_shared_access_allowed(shared_pdf, session)


def check_shared_access_allowed(shared_pdf: SharedPdf, session: Session):
    """Check if access to shared pdf is allowed based on session."""
    if shared_pdf.inactive or shared_pdf.deleted:
        return False
    
    if (
        session
        and (session.get_expiry_date() - datetime.now(timezone.utc)).total_seconds() > 0
        and shared_pdf.sessions.filter(session_key=session.session_key).count()
    ):
        return True
    else:
        return False


def get_future_datetime(time_input: str) -> datetime | None:
    """
    Gets a datetime in the future from now based on the input. Input is in the format _d_h_m, e.g. 1d0h22m.
    If input is an empty string returns None.
    """

    if not time_input:
        return None

    split_by_d = time_input.split('d')
    split_by_d_and_h = split_by_d[1].split('h')
    split_by_d_and_h_and_m = split_by_d_and_h[1].split('m')

    days = int(split_by_d[0])
    hours = int(split_by_d_and_h[0])
    minutes = int(split_by_d_and_h_and_m[0])

    now = datetime.now(timezone.utc)
    future_date = now + timedelta(days=days, hours=hours, minutes=minutes)

    return future_date
