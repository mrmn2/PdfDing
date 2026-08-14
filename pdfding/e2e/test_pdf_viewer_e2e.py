from time import sleep

from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models.pdf_models import Pdf
from pdf.services.pdf_services import PdfProcessingServices, get_or_create_pdf_reading_info
from playwright.sync_api import expect, sync_playwright
from users.service import get_demo_pdf


class TestPdfViewerE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()
        self.pdf = Pdf.objects.create(
            name='some_pdf', collection=self.user.profile.current_collection, file=get_demo_pdf()
        )

    def test_saving_page(self):
        reading_info = get_or_create_pdf_reading_info(self.pdf, self.user.profile)

        assert reading_info.current_page == 1

        with sync_playwright() as p:
            self.open(reverse('view_pdf', kwargs={'identifier': self.pdf.id}), p)
            sleep(0.5)  # we need to wait a bit for the PDF to be loaded

            self.page.locator("#pageNumber").click()
            self.page.locator("#pageNumber").press("Delete")
            self.page.locator("#pageNumber").press("3")
            self.page.locator("#pageNumber").press("Enter")

            # we need to sleep a bit, so the current page is updated
            sleep(3)

        reading_info = get_or_create_pdf_reading_info(self.pdf, self.user.profile)
        assert reading_info.current_page == 3

    def test_change_zoom(self):
        with sync_playwright() as p:
            self.open(reverse('view_pdf', kwargs={'identifier': self.pdf.id}), p)

            expect(self.page.locator("#scaleSelect")).to_have_value("auto")
            self.page.locator("#scaleSelect").click()
            self.page.locator("#scaleSelect").select_option("Page Fit")
            expect(self.page.locator("#scaleSelect")).to_have_value("page-fit")

    def test_search(self):
        reading_info = get_or_create_pdf_reading_info(self.pdf, self.user.profile)

        assert reading_info.current_page == 1

        with sync_playwright() as p:
            self.open(reverse('view_pdf', kwargs={'identifier': self.pdf.id}), p)
            sleep(0.5)  # we need to wait a bit for the PDF to be loaded

            self.page.locator("#viewFindButton").click()
            self.page.locator("#findInput").fill("Dictumst vel parturient nascetur etiam habitasse")
            self.page.locator("#findInput").press("Enter")

            # we need to sleep a bit, so the current page is updated
            sleep(3)

        reading_info = get_or_create_pdf_reading_info(self.pdf, self.user.profile)
        assert reading_info.current_page == 2

    def test_left_sidebar_pages(self):
        reading_info = get_or_create_pdf_reading_info(self.pdf, self.user.profile)

        assert reading_info.current_page == 1

        with sync_playwright() as p:
            self.open(reverse('view_pdf', kwargs={'identifier': self.pdf.id}), p)
            sleep(0.5)  # we need to wait a bit for the PDF to be loaded

            self.page.locator("#viewsManagerToggleButton").click()
            # without <2068> not working
            self.page.get_by_role("button", name="Thumbnail of Page ⁨2⁩").click()

            # we need to sleep a bit, so the current page is updated
            sleep(3)

        reading_info = get_or_create_pdf_reading_info(self.pdf, self.user.profile)
        assert reading_info.current_page == 2

    def test_save_pdf(self):
        # we use create_pdf as we wont the comments to processed
        pdf = PdfProcessingServices.create_pdf(
            "some_pdf", collection=self.user.profile.current_collection, pdf_file=get_demo_pdf()
        )
        comments = pdf.pdfcomment_set.all()

        assert comments.count() == 2

        with sync_playwright() as p:
            self.open(reverse('view_pdf', kwargs={'identifier': pdf.id}), p)
            sleep(0.5)  # we need to wait a bit for the PDF to be loaded

            self.page.locator("#editorFreeTextButton").click()
            self.page.locator(".annotationEditorLayer").first.click()
            # without <2068> not working
            self.page.get_by_role("region", name="Page ⁨1⁩").get_by_label("Text Editor").fill("1_some_new_comment")
            self.page.get_by_role("region", name="Page ⁨1⁩").get_by_label("Text Editor").press("Escape")
            self.page.locator("#savePdf").click()

            # we need to wait a bit so the pdf is processed
            sleep(0.5)

        changed_pdf = Pdf.objects.get(id=pdf.id)
        comments = changed_pdf.pdfcomment_set.all()

        assert comments.count() == 3
        assert comments.order_by("text").first().text == "1_some_new_comment"
