from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View


class SupportView(View):
    """The view for displaying the support page"""

    def get(self, request: HttpRequest):
        """Display the support page"""

        return render(request, 'support.html')


@method_decorator(login_not_required, name="dispatch")
class HealthView(View):
    """
    View for the status endpoint. Mainly used in the demo mode for restarting the demo instance every x minutes,
    as per the value of DEMO_MODE_RESTART_INTERVAL.
    """

    def get(self, request: HttpRequest):
        """Get instance status"""

        if settings.DEMO_MODE:
            user = User.objects.all().first()

            # if user was created more than DEMO_MODE_RESTART_INTERVAL minutes ago, return 400, so that PdfDing demo
            # will be restarted.
            if (
                user
                and (datetime.now(timezone.utc) - user.date_joined).total_seconds()
                > settings.DEMO_MODE_RESTART_INTERVAL * 60
            ):
                return HttpResponse(status=400)
            else:
                return HttpResponse(status=200)
        else:
            return HttpResponse(status=200)
