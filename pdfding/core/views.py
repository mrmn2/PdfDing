from datetime import datetime, timezone

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from pdf.services import workspace_services
from users.models import PdfReadingInformation


class DashboardView(View):
    """View for the Dashboard"""

    def get(self, request: HttpRequest):
        profile = request.user.profile
        ws = profile.current_workspace
        ws_pdfs = workspace_services.get_pdfs_of_workspace(ws)
        workspace_reading_infos = PdfReadingInformation.objects.filter(pdf__in=ws_pdfs)

        number_of_recents = 10
        recently_added_pdfs = ws_pdfs.order_by('-creation_date')[:number_of_recents]
        recently_viewed_pdfs = []
        recently_viewed_reading_info = workspace_reading_infos.order_by('-last_viewed_date')[:number_of_recents]
        for reading_info in recently_viewed_reading_info:
            recently_viewed_pdfs.append(reading_info.pdf)

        stats_dict = {
            'PDFs': ws_pdfs.count(),
            'Collections': profile.collections.count(),
            'Tags': profile.tags.count(),
            'Users': ws.users.count(),
            'Shared PDFs': workspace_services.get_shared_pdfs_of_workspace(ws).count(),
            'Shared Collections': workspace_services.get_shared_collections_of_workspace(ws).count(),
            'Total PDF Size': workspace_services.get_size_of_all_workspace_pdfs(ws),
        }
        return render(
            request,
            'dashboard.html',
            {
                'page': 'dashboard',
                'recently_dict': {'Recently Viewed': recently_viewed_pdfs, 'Recently Added': recently_added_pdfs},
                'stats_dict': stats_dict,
            },
        )


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
