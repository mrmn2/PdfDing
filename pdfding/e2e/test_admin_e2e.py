from django.contrib.auth.models import User
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models import Pdf
from playwright.sync_api import expect, sync_playwright


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

    def test_sidebar(self):
        with sync_playwright() as p:
            self.open(reverse("admin_overview"), p)

            expect(self.page.locator("#number_users")).to_contain_text("Users: 4")
            expect(self.page.locator("#number_pdfs")).to_contain_text("PDFs: 6")

    def test_overview(self):
        date_joined = self.user.date_joined.strftime("%b. %-d, %Y")
        # months that are not shortened do not need the dot
        if 'May' in date_joined or 'July' in date_joined or 'June' in date_joined:
            date_joined.replace('.', '')

        with sync_playwright() as p:
            self.open(reverse("admin_overview"), p)

            # test the displayed email addresses
            expect(self.page.locator("#user-1")).to_contain_text("a@a.com | Admin")
            for i in range(1, 4):
                expect(self.page.locator(f"#user-{i + 1}")).to_contain_text(f"{i}@a.com")

            # assert there is only one admin
            expect(self.page.get_by_text("| Admin")).to_have_count(1)
            for i in range(4):
                expect(self.page.get_by_text(f"Registered: {date_joined} | PDFs: {i}")).to_have_count(1)

            expect(self.page.get_by_role("button", name="Delete")).to_have_count(4)
            expect(self.page.get_by_role("button", name="Remove Admin Rights")).to_have_count(1)
            expect(self.page.get_by_role("button", name="Add Admin Rights")).to_have_count(3)

    def test_search_admin(self):
        with sync_playwright() as p:
            self.open(f"{reverse('admin_overview')}?q=%23admins", p)
            expect(self.page.locator("#user-1")).to_contain_text("a@a.com | Admin")

            expect(self.page.get_by_role("button", name="Delete")).to_have_count(1)

    def test_search_email(self):
        with sync_playwright() as p:
            self.open(f"{reverse('admin_overview')}?q=1@a.", p)
            expect(self.page.locator("#user-1")).to_contain_text("1@a.com")

            expect(self.page.get_by_role("button", name="Delete")).to_have_count(1)

    def test_sort(self):
        with sync_playwright() as p:
            self.open(f"{reverse('admin_overview')}?sort=newest", p)

            for i in range(1, 4):
                expect(self.page.locator(f"#user-{i}")).to_contain_text(f"{4 - i}@a.com")
            expect(self.page.locator("#user-4")).to_contain_text("a@a.com | Admin")

    def test_delete(self):
        with sync_playwright() as p:
            # only display one user
            self.open(f"{reverse('admin_overview')}?q=1@a.", p)

            expect(self.page.locator("body")).to_contain_text("1@a.com")
            self.page.locator("#delete-action-1").click()
            self.page.locator("#delete-confirm-1").click()

            expect(self.page.get_by_role("button", name="Delete")).to_have_count(0)

    def test_chancel_delete(self):
        with sync_playwright() as p:
            self.open(reverse('admin_overview'), p)

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
            self.open(f"{reverse('admin_overview')}?q=1@a.", p)

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
            self.open(reverse('admin_overview'), p)

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
            self.open(reverse("admin_overview"), p)
            expect(self.page.locator("body")).to_contain_text("Error 404: This page doesn't exist or is unavailable")
