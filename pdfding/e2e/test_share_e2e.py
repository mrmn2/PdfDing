from datetime import datetime, timedelta, timezone

from django.urls import reverse
from helpers import PdfDingE2ETestCase, cancel_delete_helper
from pdf.models import Pdf, SharedPdf
from playwright.sync_api import expect, sync_playwright


class NoSharedPdfE2ETestCase(PdfDingE2ETestCase):
    def test_shared_pdf_overview_no_shared_pdfs(self):
        with sync_playwright() as p:
            self.open(reverse('shared_pdf_overview'), p)
            expect(self.page.locator("body")).to_contain_text("You have not shared any PDFs yet")

    def test_add_pdf(self):
        Pdf.objects.create(owner=self.user.profile, name='some_pdf', description='description')

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            self.page.get_by_role("link", name="Share", exact=True).click()
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
            expect(self.page.locator("body")).to_contain_text("some_pdf | some_description")
            # needs to be split because of hover tooltips
            expect(self.page.locator("body")).to_contain_text("deletes in 1 day |")
            expect(self.page.locator("body")).to_contain_text("expired |")
            expect(self.page.locator("body")).to_contain_text("0/3 Views")


class SharedPdfE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()

        self.pdf = Pdf.objects.create(owner=self.user.profile, name='some_pdf', description='some_description')

    def test_sort(self):
        # create some shared pdfs
        for name in ['Some_share', 'another_share', 'this is a share', 'PDF is shared']:
            SharedPdf.objects.create(owner=self.user.profile, name=name, pdf=self.pdf)

        with sync_playwright() as p:
            self.open(f"{reverse('shared_pdf_overview')}?sort=title_desc", p)

            expect(self.page.locator("#shared-pdf-link-1")).to_have_text("this is a share")
            expect(self.page.locator("#shared-pdf-link-2")).to_have_text("Some_share")
            expect(self.page.locator("#shared-pdf-link-3")).to_have_text("PDF is shared")
            expect(self.page.locator("#shared-pdf-link-4")).to_have_text("another_share")

    def test_delete(self):
        SharedPdf.objects.create(owner=self.user.profile, name='some_shared_pdf', pdf=self.pdf)

        with sync_playwright() as p:
            self.open(f"{reverse('shared_pdf_overview')}", p)

            expect(self.page.locator("#shared-pdf-link-1")).to_have_text("some_shared_pdf")
            self.page.get_by_role("button", name="Delete").click()
            self.page.get_by_text("Confirm").click()

            expect(self.page.locator("body")).to_contain_text("You have not shared any PDFs yet")

    def test_cancel_delete(self):
        SharedPdf.objects.create(owner=self.user.profile, name='some_shared_pdf', pdf=self.pdf)

        with sync_playwright() as p:
            self.open(f"{reverse('shared_pdf_overview')}", p)

            cancel_delete_helper(self.page)

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

            self.page.get_by_role("button", name="Delete").click()
            self.page.get_by_text("Confirm").click()

            expect(self.page.locator("body")).to_contain_text("You have not shared any PDFs yet")

    def test_details_cancel_delete(self):
        shared_pdf = SharedPdf.objects.create(owner=self.user.profile, name='some_shared_pdf', pdf=self.pdf)

        with sync_playwright() as p:
            self.open(reverse('shared_pdf_details', kwargs={'identifier': shared_pdf.id}), p)

            cancel_delete_helper(self.page)
