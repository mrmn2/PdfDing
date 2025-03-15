from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models import Pdf, Tag
from playwright.sync_api import expect, sync_playwright


class PdfDetailsE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()

        # create some pdfs
        pdf = Pdf.objects.create(
            owner=self.user.profile, name='pdf_1_1', description='this is number 1', notes='some notes'
        )

        tag = Tag.objects.create(name='tag', owner=self.user.profile)
        pdf.tags.set([tag])

    def test_details(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')
        dummy_file = SimpleUploadedFile("simple.pdf", b"these are the file contents!")
        pdf.views = 1001
        pdf.number_of_pages = 10
        pdf.file = dummy_file
        pdf.save()

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'identifier': pdf.id}), p)

            expect(self.page.locator("content")).to_contain_text("pdf_1_1")
            expect(self.page.locator("#name")).to_contain_text("pdf_1_1")
            expect(self.page.locator("#description")).to_contain_text("this is number 1")
            expect(self.page.locator("#notes")).to_contain_text("some notes")
            expect(self.page.locator("#tags")).to_contain_text("#tag")
            expect(self.page.locator("#progress")).to_contain_text("10% - Page 1 of 10")
            expect(self.page.locator("#views")).to_contain_text("1001")
            expect(self.page.locator("#pdf_id")).to_contain_text(str(pdf.id))

    def test_details_progress_not_visible(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')
        pdf.views = 1001
        pdf.number_of_pages = -1
        pdf.save()

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'identifier': pdf.id}), p)

            expect(self.page.locator("content")).to_contain_text("pdf_1_1")
            expect(self.page.locator("#name")).to_contain_text("pdf_1_1")
            expect(self.page.locator("#description")).to_contain_text("this is number 1")
            expect(self.page.locator("#tags")).to_contain_text("#tag")
            expect(self.page.locator("#progress")).not_to_be_visible()
            expect(self.page.locator("content")).to_contain_text("1001")

    def test_change_details(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')
        pdf.notes = ''
        pdf.description = ''
        pdf.save()
        pdf.tags.set([])

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'identifier': pdf.id}), p)

            # edit name
            self.page.locator("#name-edit").click()
            self.page.locator("#id_name").dblclick()
            self.page.locator("#id_name").fill("other name")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("content")).to_contain_text("other name")
            expect(self.page.locator("#name")).to_contain_text("other name")

            # edit description
            expect(self.page.locator("#description")).to_contain_text("no description available")
            self.page.locator("#description-edit").click()
            self.page.locator("#id_description").click()
            self.page.locator("#id_description").fill("other description")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#description")).to_contain_text("other description")

            # edit notes
            expect(self.page.locator("#notes")).to_contain_text("no notes available")
            self.page.locator("#notes-edit").click()
            self.page.locator("#id_notes").click()
            self.page.locator("#id_notes").fill("other notes")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#notes")).to_contain_text("other notes")

            # edit tags
            expect(self.page.locator("#tags")).to_contain_text("no tags available")
            self.page.locator("#tags-edit").click()
            self.page.locator("#id_tag_string").click()
            self.page.locator("#id_tag_string").fill("other")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#tags")).to_contain_text("#other")
            # also test setting empty tag
            self.page.locator("#tags-edit").click()
            self.page.locator("#id_tag_string").click()
            self.page.locator("#id_tag_string").fill("")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#tags")).to_contain_text("no tags available")

    def test_details_star_archive(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'identifier': pdf.id}), p)

            expect(self.page.locator("#starred_icon")).not_to_be_visible()
            self.page.locator("#star").click()
            expect(self.page.locator("#starred_icon")).to_be_visible()
            self.page.locator("#star").click()
            expect(self.page.locator("#starred_icon")).not_to_be_visible()

            expect(self.page.locator("#archived_icon")).not_to_be_visible()
            self.page.locator("#archive").click()
            expect(self.page.locator("#archived_icon")).to_be_visible()
            self.page.locator("#archive").click()
            expect(self.page.locator("#archived_icon")).not_to_be_visible()

    def test_cancel_change_details(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'identifier': pdf.id}), p)

            for edit_name in ['#name-edit', '#description-edit', '#notes-edit', '#tags-edit']:
                expect(self.page.locator(edit_name)).to_contain_text("Edit")
                self.page.locator(edit_name).click()
                expect(self.page.locator(edit_name)).to_contain_text("Cancel")
                self.page.locator(edit_name).click()
                expect(self.page.locator(edit_name)).to_contain_text("Edit")

    def test_details_delete(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'identifier': pdf.id}), p)

            expect(self.page.locator("body")).to_contain_text("pdf_1_1")
            self.page.get_by_text("Delete").click()
            self.page.get_by_text("Confirm").click()

            expect(self.page.locator("body")).not_to_have_text("pdf_1_1")

    def test_details_cancel_delete(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'identifier': pdf.id}), p)

            expect(self.page.get_by_text("Confirm")).not_to_be_visible()
            expect(self.page.get_by_text("Cancel")).not_to_be_visible()
            expect(self.page.get_by_text("Delete")).to_be_visible()
            self.page.get_by_text("Delete").click()
            expect(self.page.get_by_text("Confirm")).to_be_visible()
            expect(self.page.get_by_text("Cancel")).to_be_visible()
            expect(self.page.get_by_text("Delete")).not_to_be_visible()
            self.page.get_by_text("Cancel").click()
            expect(self.page.get_by_text("Confirm")).not_to_be_visible()
            expect(self.page.get_by_text("Cancel")).not_to_be_visible()
            expect(self.page.get_by_text("Delete")).to_be_visible()
