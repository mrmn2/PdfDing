from datetime import datetime, timedelta, timezone

from django.contrib.auth.models import User
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models import Pdf, SharedPdf
from playwright.sync_api import expect, sync_playwright
from users.models import Profile


class NoSharedPdfE2ETestCase(PdfDingE2ETestCase):
    def test_shared_pdf_overview_no_shared_pdfs(self):
        with sync_playwright() as p:
            self.open(reverse('shared_pdf_overview'), p)
            expect(self.page.locator("body")).to_contain_text("You have not shared any PDFs yet")

    def test_share_pdf(self):
        Pdf.objects.create(owner=self.user.profile, name='some_pdf', description='description')

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            self.page.locator("#open-actions-1").click()
            self.page.get_by_role("link", name="share Share", exact=True).click()
            self.page.get_by_placeholder("Add Share Name").click()
            self.page.get_by_placeholder("Add Share Name").fill("some_shared_pdf")
            self.page.get_by_placeholder("Add a private description").click()
            self.page.get_by_placeholder("Add a private description").fill("some_description")
            self.page.get_by_placeholder("Protect the share with a").click()
            self.page.get_by_placeholder("Protect the share with a").fill("123")
            self.page.get_by_placeholder("Maximum number of views").click()
            self.page.get_by_placeholder("Maximum number of views").fill("3")
            self.page.get_by_placeholder("Expire in").click()
            self.page.get_by_placeholder("Expire in").fill("0d0h0m")
            self.page.get_by_placeholder("Delete in").click()
            self.page.get_by_placeholder("Delete in").fill("1d0h22m")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#shared-pdf-link-1")).to_contain_text("some_shared_pdf | inactive")
            expect(self.page.locator("body")).to_contain_text("some_pdf")
            expect(self.page.locator("body")).to_contain_text("some_description")
            # needs to be split because of hover tooltips
            expect(self.page.locator("body")).to_contain_text("deletes in 1 day")
            expect(self.page.locator("body")).to_contain_text("expired")
            expect(self.page.locator("body")).to_contain_text("0/3 Views")


class SharedPdfE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()

        self.pdf = Pdf.objects.create(owner=self.user.profile, name='some_pdf', description='some_description')

    def test_sort(self):
        self.user.profile.shared_pdf_sorting = Profile.SharedPdfSortingChoice.NAME_DESC
        self.user.profile.save()

        # create some shared pdfs
        for name in ['Some_share', 'another_share', 'this is a share', 'PDF is shared']:
            SharedPdf.objects.create(owner=self.user.profile, name=name, pdf=self.pdf)

        with sync_playwright() as p:
            self.open(reverse('shared_pdf_overview'), p)

            expect(self.page.locator("#shared-pdf-link-1")).to_have_text("this is a share")
            expect(self.page.locator("#shared-pdf-link-2")).to_have_text("Some_share")
            expect(self.page.locator("#shared-pdf-link-3")).to_have_text("PDF is shared")
            expect(self.page.locator("#shared-pdf-link-4")).to_have_text("another_share")

    def test_change_sorting(self):
        self.assertEqual(self.user.profile.shared_pdf_sorting, Profile.SharedPdfSortingChoice.NEWEST)

        with sync_playwright() as p:
            self.open(reverse("shared_pdf_overview"), p)

            self.page.locator("#sorting_settings").click()
            self.page.get_by_text("A - Z").click()

        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.shared_pdf_sorting, Profile.SharedPdfSortingChoice.NAME_ASC)

    def test_load_next_page(self):
        self.user.profile.shared_pdf_sorting = Profile.SharedPdfSortingChoice.OLDEST
        self.user.profile.save()

        for i in range(14):
            SharedPdf.objects.create(owner=self.user.profile, name=f'shared_{i}', pdf=self.pdf)

        with sync_playwright() as p:
            self.open(reverse('shared_pdf_overview'), p)
            expect(self.page.locator("#shared-pdf-12")).to_be_visible()
            expect(self.page.locator("#shared-pdf-13")).not_to_be_visible()

            self.page.locator("#next_page_1_toggle").click()
            expect(self.page.locator("#shared-pdf-13")).to_be_visible()
            expect(self.page.locator("#shared-pdf-13")).to_contain_text('shared_12')
            expect(self.page.locator("#next_page_2_toggle")).not_to_be_visible()

    def test_delete(self):
        SharedPdf.objects.create(owner=self.user.profile, name='some_shared_pdf', pdf=self.pdf)

        with sync_playwright() as p:
            self.open(f"{reverse('shared_pdf_overview')}", p)

            expect(self.page.locator("#shared-pdf-link-1")).to_have_text("some_shared_pdf")
            self.page.locator("#delete_1 a").filter(has_text="Delete").click()
            self.page.locator("#delete_1").get_by_text("Confirm").click()

            expect(self.page.locator("body")).to_contain_text("You have not shared any PDFs yet")

    def test_cancel_delete(self):
        SharedPdf.objects.create(owner=self.user.profile, name='some_shared_pdf', pdf=self.pdf)

        with sync_playwright() as p:
            self.open(f"{reverse('shared_pdf_overview')}", p)

            self.page.locator("#delete_1 a").filter(has_text="Delete").click()
            expect(self.page.locator("#delete_1").get_by_text("Cancel")).to_be_visible()
            expect(self.page.locator("#delete_1").get_by_text("Confirm")).to_be_visible()
            expect(self.page.locator("#delete_1 a").filter(has_text="Delete")).not_to_be_visible()
            self.page.locator("#delete_1").get_by_text("Cancel").click()
            expect(self.page.locator("#delete_1 a").filter(has_text="Delete")).to_be_visible()
            expect(self.page.locator("#delete_1 a").filter(has_text="Cancel")).not_to_be_visible()
            expect(self.page.locator("#delete_1").get_by_text("Confirm")).not_to_be_visible()

    def test_details(self):
        shared_pdf = SharedPdf.objects.create(
            owner=self.user.profile,
            name='some_shared_pdf',
            description="some_description",
            pdf=self.pdf,
            max_views=1002,
            password='password',
            deletion_date=datetime.now(timezone.utc) + timedelta(days=1, minutes=5),
            expiration_date=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        shared_pdf.views = 1001
        shared_pdf.save()

        with sync_playwright() as p:
            self.open(reverse('shared_pdf_details', kwargs={'identifier': shared_pdf.id}), p)

            expect(self.page.locator("content")).to_contain_text("some_shared_pdf | inactive")
            expect(self.page.locator("#name")).to_contain_text("some_shared_pdf")
            expect(self.page.locator("content")).to_contain_text(f"pdf/shared/{shared_pdf.id}")
            expect(self.page.locator("#description")).to_contain_text("some_description")
            expect(self.page.locator("#pdf")).to_contain_text("some_pdf")
            expect(self.page.locator("content")).to_contain_text("1001")
            expect(self.page.locator("#password")).to_contain_text("***")
            expect(self.page.locator("#max_views")).to_contain_text("1002")
            expect(self.page.locator("#expiration_date")).to_contain_text("expired")
            expect(self.page.locator("#deletion_date")).to_contain_text("deletes in 1 day")

    def test_change_details(self):
        shared_pdf = SharedPdf.objects.create(
            owner=self.user.profile,
            name='some_shared_pdf',
            description="some_description",
            pdf=self.pdf,
            max_views=1002,
            password='password',
            deletion_date=datetime.now(timezone.utc) + timedelta(days=1, minutes=5),
            expiration_date=datetime.now(timezone.utc) - timedelta(minutes=5),
        )

        # also test changing from inactive to active
        with sync_playwright() as p:
            self.open(reverse('shared_pdf_details', kwargs={'identifier': shared_pdf.id}), p)

            self.page.locator("#name-edit").click()
            self.page.locator("#id_name").dblclick()
            self.page.locator("#id_name").fill("other name")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("content")).to_contain_text("other name | inactive")
            expect(self.page.locator("#name")).to_contain_text("other name")
            self.page.locator("#description-edit").click()
            self.page.locator("#id_description").click()
            self.page.locator("#id_description").fill("other description")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#description")).to_contain_text("other description")
            self.page.locator("#password-edit").click()
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#password")).to_contain_text("not set")
            self.page.locator("#max_views-edit").click()
            self.page.locator("#id_max_views").click()
            self.page.locator("#id_max_views").fill("5")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#max_views")).to_contain_text("5")
            self.page.locator("#expiration_date-edit").click()
            self.page.get_by_placeholder("e.g. 1d0h22m").click()
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#expiration_date")).to_contain_text("expires never")
            expect(self.page.locator("content")).not_to_contain_text('inactive')
            self.page.locator("#deletion_date-edit").click()
            self.page.get_by_placeholder("e.g. 1d0h22m").click()
            self.page.get_by_placeholder("e.g. 1d0h22m").fill("0d0h5m")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#deletion_date")).to_contain_text("deletes in 4 minutes")

    def test_cancel_change_details(self):
        shared_pdf = SharedPdf.objects.create(
            owner=self.user.profile, name='some_shared_pdf', description="some_description", pdf=self.pdf
        )

        with sync_playwright() as p:
            self.open(reverse('shared_pdf_details', kwargs={'identifier': shared_pdf.id}), p)

            for edit_name in ['#name-edit', '#description-edit']:
                expect(self.page.locator(edit_name)).to_contain_text("Edit")
                self.page.locator(edit_name).click()
                expect(self.page.locator(edit_name)).to_contain_text("Cancel")
                self.page.get_by_role("link", name="Cancel").click()
                expect(self.page.locator(edit_name)).to_contain_text("Edit")

    def test_details_delete(self):
        shared_pdf = SharedPdf.objects.create(owner=self.user.profile, name='some_shared_pdf', pdf=self.pdf)

        with sync_playwright() as p:
            self.open(reverse('shared_pdf_details', kwargs={'identifier': shared_pdf.id}), p)

            self.page.locator("#delete_shared").click()
            self.page.get_by_text("Confirm").click()

            expect(self.page.locator("body")).to_contain_text("You have not shared any PDFs yet")

    def test_details_cancel_delete(self):
        shared_pdf = SharedPdf.objects.create(owner=self.user.profile, name='some_shared_pdf', pdf=self.pdf)

        with sync_playwright() as p:
            self.open(reverse('shared_pdf_details', kwargs={'identifier': shared_pdf.id}), p)

            expect(self.page.get_by_text("Confirm")).not_to_be_visible()
            expect(self.page.get_by_text("Cancel")).not_to_be_visible()
            expect(self.page.locator("#delete_shared")).to_be_visible()
            self.page.locator("#delete_shared").click()
            expect(self.page.get_by_text("Confirm")).to_be_visible()
            expect(self.page.get_by_text("Cancel")).to_be_visible()
            expect(self.page.locator("#delete_shared")).not_to_be_visible()
            self.page.get_by_text("Cancel").click()
            expect(self.page.get_by_text("Confirm")).not_to_be_visible()
            expect(self.page.get_by_text("Cancel")).not_to_be_visible()
            expect(self.page.locator("#delete_shared")).to_be_visible()
