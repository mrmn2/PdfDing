from unittest.mock import patch

from allauth.mfa.models import Authenticator
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models.pdf_models import Pdf
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
                Pdf.objects.create(collection=user.profile.current_collection, name=f"pdf_{j}")

    def test_instance_info(self):
        with sync_playwright() as p:
            self.open(reverse("instance_info"), p)

            expect(self.page.locator("#number_of_users")).to_contain_text("4")
            expect(self.page.locator("#number_of_pdfs")).to_contain_text("6")
            expect(self.page.locator("#current_version")).to_contain_text("DEV")

    def test_overview(self):
        self.user.profile.user_sorting = Profile.UserSortingChoice.EMAIL_ASC
        self.user.profile.save()

        with sync_playwright() as p:
            self.open(reverse("user_overview"), p)

            expect(self.page.locator("#user-4")).to_contain_text("a@a.com")
            expect(self.page.locator("#user-4-admin-icon")).to_be_visible()

            for i in range(1, 4):
                expect(self.page.locator(f"#user-{i}")).to_contain_text(f"{i}@a.com")
                expect(self.page.locator(f"#user-{i}-admin-icon")).not_to_be_visible()

    def test_change_sorting(self):
        self.assertEqual(self.user.profile.user_sorting, Profile.UserSortingChoice.NEWEST)

        with sync_playwright() as p:
            self.open(reverse("user_overview"), p)

            self.page.locator("#sorting_settings").click()
            self.page.get_by_text("A - Z").click()

        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.user_sorting, Profile.UserSortingChoice.EMAIL_ASC)

    @patch('users.models.Profile.get_items_per_page', return_value=12)
    def test_load_next_page(self, mock_get_items_per_page):
        self.user.profile.user_sorting = Profile.UserSortingChoice.OLDEST
        self.user.profile.save()

        for i in range(4, 14):
            User.objects.create_user(username=i, password="password", email=f"{i}@a.com")

        with sync_playwright() as p:
            self.open(reverse('user_overview'), p)
            expect(self.page.locator("#user-12")).to_be_visible()
            expect(self.page.locator("#user-13")).not_to_be_visible()

            self.page.locator("#next_page_1_toggle").click()
            expect(self.page.locator("#user-13")).to_be_visible()
            expect(self.page.locator("#user-13")).to_contain_text('12@a.com')
            expect(self.page.locator("#next_page_2_toggle")).not_to_be_visible()

    def test_search_admin(self):
        with sync_playwright() as p:
            self.open(f"{reverse('user_overview')}?tags=admin", p)
            expect(self.page.locator("#user-1")).to_contain_text("a@a.com")
            for i in range(2, 5):
                expect(self.page.locator(f"#user-{i}")).not_to_be_visible()

    def test_search_email(self):
        with sync_playwright() as p:
            self.open(f"{reverse('user_overview')}?search=1@a.", p)
            expect(self.page.locator("#user-1")).to_contain_text("1@a.com")
            expect(self.page.locator("#user-2")).not_to_be_visible()

    def test_search_filters(self):
        with sync_playwright() as p:
            self.open(f"{reverse('user_overview')}?search=a@a&tags=admin", p)

            # check that filters have the correct text and are visible
            expect(self.page.locator("#search_filter")).to_contain_text("a@a")
            expect(self.page.locator("#tag_admin_filter")).to_contain_text("#admin")
            expect(self.page.locator("#search_filter")).to_be_visible()
            expect(self.page.locator("#tag_admin_filter")).to_be_visible()

            # check that filters are invisible
            self.page.locator("#tag_admin_filter_close").click()
            self.page.locator("#search_filter_close").click()
            expect(self.page.locator("#search_filter")).not_to_be_visible()
            expect(self.page.locator("#tag_admin_filter")).not_to_be_visible()

    def test_sort(self):
        self.user.profile.user_sorting = Profile.UserSortingChoice.NEWEST
        self.user.profile.save()

        with sync_playwright() as p:
            self.open(reverse('user_overview'), p)

            for i in range(1, 4):
                expect(self.page.locator(f"#user-{i}")).to_contain_text(f"{4 - i}@a.com")
            expect(self.page.locator("#user-4")).to_contain_text("a@a.com")

    def test_open_close_action(self):
        with sync_playwright() as p:
            self.open(f"{reverse('user_overview')}", p)

            expect(self.page.locator("#actions-1")).not_to_be_visible()
            self.page.locator("#open-actions-1").click()
            expect(self.page.locator("#actions-1")).to_be_visible()
            self.page.locator("body").click()
            expect(self.page.locator("#actions-1")).not_to_be_visible()

    def test_delete(self):
        with sync_playwright() as p:
            # only display one user
            self.open(f"{reverse('user_overview')}?search=3@a.", p)

            expect(self.page.locator("body")).to_contain_text("3@a.com")
            self.page.locator("#open-actions-1").click()
            self.page.locator("#delete-1").click()
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("body")).not_to_contain_text("3@a.com")

    def test_chancel_delete(self):
        with sync_playwright() as p:
            # only display one user
            self.open(f"{reverse('user_overview')}", p)

            expect(self.page.locator("#delete_user_modal")).not_to_be_visible()
            self.page.locator("#open-actions-1").click()
            self.page.locator("#delete-1").click()
            expect(self.page.locator("#delete_user_modal")).to_be_visible()
            self.page.get_by_text("Cancel").click()
            expect(self.page.locator("#delete_user_modal")).not_to_be_visible()

    def test_add_remove_admin_rights(self):
        with sync_playwright() as p:
            self.open(f"{reverse('user_overview')}?search=1@a.", p)
            expect(self.page.locator("body")).to_contain_text("1@a.com")
            expect(self.page.locator("#user-1-admin-icon")).not_to_be_visible()
            self.page.locator("#open-actions-1").click()
            expect(self.page.locator("#actions-1")).to_contain_text("Add Admin Rights")
            self.page.locator("#adjust-admin-rights-1").click()
            expect(self.page.locator("#user-1-admin-icon")).to_be_visible()
            self.page.locator("#open-actions-1").click()
            expect(self.page.locator("#actions-1")).to_contain_text("Remove Admin Rights")
            self.page.locator("#adjust-admin-rights-1").click()
            expect(self.page.locator("#user-1-admin-icon")).not_to_be_visible()
            self.page.locator("#open-actions-1").click()
            expect(self.page.locator("#actions-1")).to_contain_text("Add Admin Rights")

    def test_create_user(self):
        with sync_playwright() as p:
            self.open(reverse('user_overview'), p)
            expect(self.page.locator("body")).not_to_contain_text("b@a.com")

            self.page.get_by_role("link", name="Add User").click()
            self.page.get_by_role("textbox", name="Email:").click()
            self.page.get_by_role("textbox", name="Email:").fill("b@a.com")
            self.page.get_by_role("textbox", name="Password:").click()
            self.page.get_by_role("textbox", name="Password:").fill("pw")
            self.page.get_by_role("textbox", name="Password2:").click()
            self.page.get_by_role("textbox", name="Password2:").fill("pw")
            self.page.get_by_role("button", name="Submit").click()

            expect(self.page.locator("body")).to_contain_text("b@a.com")

    def test_set_password(self):
        with sync_playwright() as p:
            self.open(f"{reverse('user_overview')}?search=1@a.", p)
            self.page.locator("#open-actions-1").click()
            self.page.locator("#set-pw-1").click()
            self.page.get_by_role("textbox", name="Password:").click()
            self.page.get_by_role("textbox", name="Password:").fill("1")
            self.page.get_by_role("textbox", name="Password2:").click()
            self.page.get_by_role("textbox", name="Password2:").fill("1")
            self.page.get_by_role("button", name="Submit").click()

        changed_user = User.objects.get(email="1@a.com")

        assert check_password("1", changed_user.password)

    def test_reset_mfa(self):
        user = User.objects.get(email="1@a.com")
        Authenticator.objects.create(user=user, type='totp', data={})

        assert user.profile.mfa_activated

        with sync_playwright() as p:
            self.open(f"{reverse('user_overview')}?search=1@a.", p)
            self.page.locator("#open-actions-1").click()
            self.page.locator("#reset-mfa-1").click()

        changed_user = User.objects.get(email="1@a.com")
        assert not changed_user.profile.mfa_activated


class NoAdminE2ETestCase(PdfDingE2ETestCase):
    def test_404(self):
        with sync_playwright() as p:
            self.open(reverse("user_overview"), p)
            expect(self.page.locator("body")).to_contain_text("Error 404: This page doesn't exist or is unavailable")
