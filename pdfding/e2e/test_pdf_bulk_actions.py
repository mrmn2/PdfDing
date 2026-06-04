from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models.pdf_models import Pdf
from playwright.sync_api import expect, sync_playwright

from pdfding.pdf.services.workspace_services import create_collection


class PdfBulkActionsE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()

        # create some pdfs
        for i in range(2):
            Pdf.objects.create(
                collection=self.user.profile.current_collection,
                name=f'pdf_{i+1}',
            )

    def test_archive(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("body")).to_contain_text("pdf_1")
            expect(self.page.locator("body")).to_contain_text("pdf_2")

            self.page.locator("#bulk_edit").click()
            self.page.locator("#select_bulk_action").select_option("archive")
            # for some reason normal checking via playwright does not work with alpine JS
            # thus we use the all functionality
            self.page.locator("#bulk_edit_menu").get_by_text("All").click()
            self.page.get_by_role("button", name="Execute").click()

            expect(self.page.locator("body")).not_to_contain_text("pdf_1")
            expect(self.page.locator("body")).not_to_contain_text("pdf_2")

            self.page.get_by_role("link", name="Archive").click()
            expect(self.page.locator("body")).to_contain_text("pdf_1")
            expect(self.page.locator("body")).to_contain_text("pdf_2")

    def test_star(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("body")).to_contain_text("pdf_1")
            expect(self.page.locator("body")).to_contain_text("pdf_2")

            self.page.locator("#bulk_edit").click()
            self.page.locator("#select_bulk_action").select_option("star")
            # for some reason normal checking via playwright does not work with alpine JS
            # thus we use the all functionality
            self.page.locator("#bulk_edit_menu").get_by_text("All").click()
            self.page.get_by_role("button", name="Execute").click()

            self.page.get_by_role("link", name="Starred").click()
            expect(self.page.locator("body")).to_contain_text("pdf_1")
            expect(self.page.locator("body")).to_contain_text("pdf_2")

    def test_delete_no_confirmation(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("body")).to_contain_text("pdf_1")
            expect(self.page.locator("body")).to_contain_text("pdf_2")

            self.page.locator("#bulk_edit").click()
            self.page.locator("#select_bulk_action").select_option("delete")
            self.page.locator("#delete_confirmation").select_option("no")
            # for some reason normal checking via playwright does not work with alpine JS
            # thus we use the all functionality
            self.page.locator("#bulk_edit_menu").get_by_text("All").click()
            self.page.get_by_role("button", name="Execute").click()

            expect(self.page.locator("body")).to_contain_text("pdf_1")
            expect(self.page.locator("body")).to_contain_text("pdf_2")

        assert Pdf.objects.filter(name='pdf_1').exists()
        assert Pdf.objects.filter(name='pdf_2').exists()

    def test_delete(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("body")).to_contain_text("pdf_1")
            expect(self.page.locator("body")).to_contain_text("pdf_2")

            self.page.locator("#bulk_edit").click()
            self.page.locator("#select_bulk_action").select_option("delete")
            self.page.locator("#delete_confirmation").select_option("yes")
            # for some reason normal checking via playwright does not work with alpine JS
            # thus we use the all functionality
            self.page.locator("#bulk_edit_menu").get_by_text("All").click()
            self.page.get_by_role("button", name="Execute").click()

            expect(self.page.locator("body")).not_to_contain_text("pdf_1")
            expect(self.page.locator("body")).not_to_contain_text("pdf_2")

        assert not Pdf.objects.filter(name='pdf_1').exists()
        assert not Pdf.objects.filter(name='pdf_2').exists()

    def test_set_tags(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("body")).not_to_contain_text("some_tag")

            self.page.locator("#bulk_edit").click()
            self.page.locator("#select_bulk_action").select_option("set_tags")
            self.page.get_by_role("textbox", name="Enter tags").click()
            self.page.get_by_role("textbox", name="Enter tags").fill("some_tag")

            # for some reason normal checking via playwright does not work with alpine JS
            # thus we use the all functionality
            self.page.locator("#bulk_edit_menu").get_by_text("All").click()
            self.page.get_by_role("button", name="Execute").click()

            expect(self.page.locator("body")).to_contain_text("some_tag")

        for pdf_name in ['pdf_1', 'pdf_2']:
            pdf = Pdf.objects.get(name=pdf_name)

            assert pdf.tags.count() == 1
            assert pdf.tags.filter(name='some_tag').exists()

    def test_set_collection(self):
        other_collection = create_collection(self.user.profile.current_workspace, collection_name='other_collection')

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("body")).not_to_contain_text("some_tag")

            self.page.locator("#bulk_edit").click()
            self.page.locator("#select_bulk_action").select_option("set_collection")
            self.page.locator("#select_collection").select_option(str(other_collection.id))

            # for some reason normal checking via playwright does not work with alpine JS
            # thus we use the all functionality
            self.page.locator("#bulk_edit_menu").get_by_text("All").click()
            self.page.get_by_role("button", name="Execute").click()

        for pdf_name in ['pdf_1', 'pdf_2']:
            pdf = Pdf.objects.get(name=pdf_name)

            assert pdf.collection == other_collection
