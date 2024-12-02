from admin.service import get_latest_version
from core import base_views
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.db.models.functions import Lower
from django.http import Http404, HttpRequest
from django.shortcuts import redirect
from django.views import View
from django_htmx.http import HttpResponseClientRefresh
from pdf.models import Pdf


class BaseAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_superuser and self.request.user.is_staff:
            return True
        else:
            raise Http404("Given query not found...")


class BaseAdminMixin:
    obj_name = 'user'


class OverviewMixin(BaseAdminMixin):
    @staticmethod
    def get_sorting_dict():
        """
        Get the sorting dict which describes the sorting in the overview page.
        """

        sorting_dict = {
            '': 'date_joined',
            'newest': '-date_joined',
            'oldest': 'date_joined',
            'title_asc': Lower('email'),
            'title_desc': Lower('email').desc(),
        }

        return sorting_dict

    @staticmethod
    def filter_objects(request: HttpRequest) -> QuerySet:
        """
        Filter the PDFs when performing a search in the overview.
        """

        users = User.objects.all()

        raw_search_query = request.GET.get('q', '')

        if raw_search_query:
            search_words = raw_search_query.split()

            if '#admins' in search_words:
                users = users.filter(is_superuser=True)
                search_words.remove('#admins')

            search_query = ' '.join(search_words)
            users = users.filter(email__icontains=search_query)

        return users

    @staticmethod
    def get_extra_context(request: HttpRequest) -> dict:
        """get further information that needs to be passed to the template."""

        number_of_users = User.objects.all().count()
        number_of_pdfs = Pdf.objects.all().count()
        latest_version = get_latest_version()

        extra_context = {
            'raw_search_query': request.GET.get('q', ''),
            'number_of_users': number_of_users,
            'number_of_pdfs': number_of_pdfs,
            'current_version': settings.VERSION,
            'latest_version': latest_version,
        }

        return extra_context


class AdminMixin(BaseAdminMixin):
    @staticmethod
    def get_object(_, identifier: str):
        user = User.objects.get(id=identifier)

        return user


class Overview(BaseAdminRequiredMixin, OverviewMixin, base_views.BaseOverview):
    """
    View for the PDF overview page. This view performs the searching and sorting of the PDFs. It's also responsible for
    paginating the PDFs.
    """


class DeleteProfile(BaseAdminRequiredMixin, AdminMixin, base_views.BaseDelete):
    """View for deleting a user profile"""


class AdjustAdminRights(BaseAdminRequiredMixin, View):
    """View for adjusting the admin rights"""

    def post(self, request: HttpRequest, identifier: str):
        """Delete the user"""

        if request.htmx:
            user = User.objects.get(id=identifier)

            if user.is_staff and user.is_superuser:
                user.is_staff = False
                user.is_superuser = False
            else:
                user.is_staff = True
                user.is_superuser = True

            user.save()

            return HttpResponseClientRefresh()

        return redirect('admin_overview')
