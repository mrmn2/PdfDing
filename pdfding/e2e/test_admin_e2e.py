from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models import Pdf
from playwright.sync_api import expect, sync_playwright
from users.models import Profile


class AdminE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        # create some users and pdfs
        for i in range(1, 4):
            user = User.objects.create_user(username=i, password="password", email=f"{i}@a.com")

            for j in range(1, i + 1):
                Pdf.objects.create(owner=user.profile, name=f"pdf_{j}")

    def test_instance_info(self):
        with sync_playwright() as p:
            self.open(reverse("instance_info"), p)

            expect(self.page.locator("#number_of_users")).to_contain_text("4")
            expect(self.page.locator("#number_of_pdfs")).to_contain_text("6")
            expect(self.page.locator("#current_version")).to_contain_text("DEV")

    def test_overview(self):
        self.user.profile.user_sorting = Profile.UserSortingChoice.EMAIL_ASC
        self.user.profile.save()

        date_joined = self.user.date_joined.strftime("%b. %-d, %Y")
        # months that are not shortened do not need the dot
        if 'May' in date_joined or 'July' in date_joined or 'June' in date_joined:
            date_joined.replace('.', '')

        with sync_playwright() as p:
            self.open(reverse("user_overview"), p)

            # test the displayed email addresses
            for i in range(1, 4):
                expect(self.page.locator(f"#user-{i}")).to_contain_text(f"{i}@a.com")

            expect(self.page.locator("#user-4")).to_contain_text("a@a.com | Admin")

            # assert there is only one admin
            expect(self.page.get_by_text("| Admin")).to_have_count(1)
            for i in range(4):
                expect(self.page.get_by_text(f"Registered: {date_joined} | PDFs: {i}")).to_have_count(1)

            expect(self.page.get_by_text("Delete")).to_have_count(4)
            expect(self.page.get_by_text("Remove Admin Rights")).to_have_count(1)
            expect(self.page.get_by_text("Add Admin Rights")).to_have_count(3)

    def test_change_sorting(self):
        self.assertEqual(self.user.profile.user_sorting, Profile.UserSortingChoice.NEWEST)

        with sync_playwright() as p:
            self.open(reverse("user_overview"), p)

            self.page.locator("#sorting_settings").click()
            self.page.get_by_text("A - Z").click()

        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.user_sorting, Profile.UserSortingChoice.EMAIL_ASC)

    def test_load_next_page(self):
        self.user.profile.user_sorting = Profile.UserSortingChoice.OLDEST
        self.user.profile.save()

        for i in range(4, 17):
            User.objects.create_user(username=i, password="password", email=f"{i}@a.com")

        with sync_playwright() as p:
            self.open(reverse('user_overview'), p)
            expect(self.page.locator("#user-15")).to_be_visible()
            expect(self.page.locator("#user-16")).not_to_be_visible()

            self.page.locator("#next_page_1_toggle").click()
            expect(self.page.locator("#user-16")).to_be_visible()
            expect(self.page.locator("#user-16")).to_contain_text('15@a.com')
            expect(self.page.locator("#next_page_2_toggle")).not_to_be_visible()

    @patch('admin.views.get_latest_version', return_value='0.0.0')
    def test_new_version_available(self, mock_get_latest_version):
        with sync_playwright() as p:
            self.open(reverse("instance_info"), p)

            expect(self.page.locator("content")).to_contain_text("New Version Available!")
            expect(self.page.locator("#new_version")).to_contain_text("0.0.0")

    @patch('admin.views.get_latest_version', return_value='DEV')
    def test_new_version_same(self, mock_get_latest_version):
        with sync_playwright() as p:
            self.open(reverse("instance_info"), p)

            expect(self.page.locator("content")).not_to_contain_text("New Version Available!")

    @patch('admin.views.get_latest_version', return_value='0.0.0')
    @override_settings(VERSION='UNKNOWN')
    def test_new_version_unknown(self, mock_get_latest_version):
        with sync_playwright() as p:
            self.open(reverse("instance_info"), p)

            expect(self.page.locator("content")).not_to_contain_text("New Version Available!")

    @patch('admin.views.get_latest_version', return_value='')
    def test_new_version_empty(self, mock_get_latest_version):
        with sync_playwright() as p:
            self.open(reverse("instance_info"), p)

            expect(self.page.locator("content")).not_to_contain_text("New Version Available!")

    def test_search_admin(self):
        with sync_playwright() as p:
            self.open(f"{reverse('user_overview')}?tags=admin", p)
            expect(self.page.locator("#user-1")).to_contain_text("a@a.com | Admin")

            expect(self.page.get_by_text("Delete")).to_have_count(1)

    def test_search_email(self):
        with sync_playwright() as p:
            self.open(f"{reverse('user_overview')}?search=1@a.", p)
            expect(self.page.locator("#user-1")).to_contain_text("1@a.com")

            expect(self.page.get_by_text("Delete")).to_have_count(1)

    def test_search_filters(self):
        with sync_playwright() as p:
            self.open(f"{reverse('user_overview')}?search=a@a&tags=admin", p)

            # check that filters have the correct text and are visible
            expect(self.page.locator("#search_filter")).to_contain_text("a@a")
            expect(self.page.locator("#tag_admin_filter")).to_contain_text("#admin")
            expect(self.page.locator("#search_filter")).to_be_visible()
            expect(self.page.locator("#tag_admin_filter")).to_be_visible()

            # check that filters are invisible
            self.page.locator("#search_filter").get_by_role("img").click()
            self.page.locator("#tag_admin_filter").get_by_role("img").click()
            expect(self.page.locator("#search_filter")).not_to_be_visible()
            expect(self.page.locator("#tag_admin_filter")).not_to_be_visible()

    def test_sort(self):
        self.user.profile.user_sorting = Profile.UserSortingChoice.NEWEST
        self.user.profile.save()

        with sync_playwright() as p:
            self.open(reverse('user_overview'), p)

            for i in range(1, 4):
                expect(self.page.locator(f"#user-{i}")).to_contain_text(f"{4 - i}@a.com")
            expect(self.page.locator("#user-4")).to_contain_text("a@a.com | Admin")

    def test_delete(self):
        with sync_playwright() as p:
            # only display one user
            self.open(f"{reverse('user_overview')}?q=1@a.", p)

            expect(self.page.locator("body")).to_contain_text("1@a.com")
            self.page.locator("#delete-action-1").click()
            self.page.locator("#delete-confirm-1").click()

            expect(self.page.get_by_role("button", name="Delete")).to_have_count(0)

    def test_chancel_delete(self):
        with sync_playwright() as p:
            self.open(reverse('user_overview'), p)

            expect(self.page.locator("#delete-confirm-1")).not_to_be_visible()
            expect(self.page.locator("#delete-cancel-1")).not_to_be_visible()
            expect(self.page.locator("#delete-action-1")).to_be_visible()
            self.page.locator("#delete-action-1").click()
            expect(self.page.locator("#delete-confirm-1")).to_be_visible()
            expect(self.page.locator("#delete-cancel-1")).to_be_visible()
            expect(self.page.locator("#delete-action-1")).not_to_be_visible()
            self.page.locator("#delete-cancel-1").click()
            expect(self.page.locator("#delete-confirm-1")).not_to_be_visible()
            expect(self.page.locator("#delete-cancel-1")).not_to_be_visible()
            expect(self.page.locator("#delete-action-1")).to_be_visible()

    def test_add_remove_admin_rights(self):
        with sync_playwright() as p:
            # only display one user
            self.open(f"{reverse('user_overview')}?search=1@a.", p)

            expect(self.page.locator("body")).to_contain_text("1@a.com")
            expect(self.page.locator("#admin-action-1")).to_contain_text("Add Admin Rights")
            expect(self.page.locator("body")).not_to_contain_text("| Admin")

            self.page.locator("#admin-action-1").click()
            self.page.locator("#admin-confirm-1").click()

            expect(self.page.locator("body")).to_contain_text("1@a.com | Admin")
            expect(self.page.locator("#admin-action-1")).to_contain_text("Remove Admin Rights")

            self.page.locator("#admin-action-1").click()
            self.page.locator("#admin-confirm-1").click()

            expect(self.page.locator("body")).to_contain_text("1@a.com")
            expect(self.page.locator("body")).not_to_contain_text("| Admin")
            expect(self.page.locator("#admin-action-1")).to_contain_text("Add Admin Rights")

    def test_admin_action_cancel(self):
        with sync_playwright() as p:
            self.open(reverse('user_overview'), p)

            expect(self.page.locator("#admin-confirm-1")).not_to_be_visible()
            expect(self.page.locator("#admin-cancel-1")).not_to_be_visible()
            expect(self.page.locator("#admin-action-1")).to_be_visible()
            self.page.locator("#admin-action-1").click()
            expect(self.page.locator("#admin-confirm-1")).to_be_visible()
            expect(self.page.locator("#admin-cancel-1")).to_be_visible()
            expect(self.page.locator("#admin-action-1")).not_to_be_visible()
            self.page.locator("#admin-cancel-1").click()
            expect(self.page.locator("#admin-confirm-1")).not_to_be_visible()
            expect(self.page.locator("#admin-cancel-1")).not_to_be_visible()
            expect(self.page.locator("#admin-action-1")).to_be_visible()


class NoAdminE2ETestCase(PdfDingE2ETestCase):
    def test_404(self):
        with sync_playwright() as p:
            self.open(reverse("user_overview"), p)
            expect(self.page.locator("body")).to_contain_text("Error 404: This page doesn't exist or is unavailable")
