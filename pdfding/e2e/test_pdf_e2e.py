from pathlib import Path
from unittest.mock import patch

from django.urls import reverse
from playwright.sync_api import sync_playwright, expect

from helpers import PdfDingE2ETestCase
from pdf.models import Pdf, Tag


class NoPdfE2ETestCase(PdfDingE2ETestCase):
    def test_pdf_overview_no_pdfs(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("body")).to_contain_text("You have no PDFs yet")
            expect(self.page.locator("body")).to_contain_text("Get started by adding PDFs.")

    @patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_add_pdf(self, mock_from_buffer):
        # this also tests the overview

        # just use some dummy file for uploading
        dummy_file_path = Path(__file__).parent / 'dummy.pdf'
        with open(dummy_file_path, 'w') as f:
            f.write('Some text')

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            self.page.get_by_role("link", name="Add PDF").click()
            self.page.get_by_placeholder("Add PDF Name").click()
            self.page.get_by_placeholder("Add PDF Name").fill("Some Name")
            self.page.get_by_placeholder("Add Description").click()
            self.page.get_by_placeholder("Add Description").fill("Some Description")
            self.page.get_by_label("File:").click()
            self.page.get_by_label("File:").set_input_files(dummy_file_path)
            self.page.get_by_placeholder("Add Tags").click()
            self.page.get_by_placeholder("Add Tags").fill("Some Tag")
            self.page.get_by_role("button", name="Submit").click()

            # check center
            expect(self.page.locator("body")).to_contain_text("Some Name")
            expect(self.page.locator("body")).to_contain_text("#some")
            expect(self.page.locator("body")).to_contain_text("#tag")
            expect(self.page.locator("body")).to_contain_text("Some Description")
            expect(self.page.locator("body")).to_contain_text("now |")
            # check tag sidebar
            expect(self.page.get_by_role("link", name="some", exact=True)).to_contain_text("some")
            expect(self.page.get_by_role("link", name="tag", exact=True)).to_contain_text("tag")
        dummy_file_path.unlink()


class PdfE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()

        # create some pdfs
        for i in range(1, 15):
            pdf = Pdf.objects.create(
                owner=self.user.profile, name=f'pdf_{i % 5}_{i}', description=f'this is number {i}'
            )

            # add a tag to pdf 1, 6
            if i % 5 == 1:
                tag = Tag.objects.create(name='tag', owner=self.user.profile)
                pdf.tags.set([tag])

    def test_search_tags(self):
        with sync_playwright() as p:
            # display the three pdfs with the tag 'tag'
            self.open(f"{reverse('pdf_overview')}?q=%23tag", p)

            delete_buttons = self.page.get_by_role("button", name="Delete")

            # assert there are three pdfs with a tag
            expect(delete_buttons).to_have_count(3)
            # pdfs are by default sorted from newest to oldest
            expect(self.page.locator("#pdf-link-1")).to_contain_text("pdf_1_11")
            expect(self.page.locator("#pdf-link-2")).to_contain_text("pdf_1_6")
            expect(self.page.locator("#pdf-link-3")).to_contain_text("pdf_1_1")

    def test_search_names(self):
        with sync_playwright() as p:
            # display the three pdfs with the tag 'tag'
            self.open(f"{reverse('pdf_overview')}?q=pdf_2_", p)

            delete_buttons = self.page.get_by_role("button", name="Delete")

            # assert there are three pdfs with a tag
            expect(delete_buttons).to_have_count(3)
            # pdfs are by default sorted from newest to oldest
            expect(self.page.locator("#pdf-link-1")).to_contain_text("pdf_2_12")
            expect(self.page.locator("#pdf-link-2")).to_contain_text("pdf_2_7")
            expect(self.page.locator("#pdf-link-3")).to_contain_text("pdf_2_2")

    def test_search_names_and_tags(self):
        with sync_playwright() as p:
            # display the three pdfs with the tag 'tag'
            self.open(f"{reverse('pdf_overview')}?q=pdf_1_1+%23tag", p)

            delete_buttons = self.page.get_by_role("button", name="Delete")

            # assert there are three pdfs with a tag
            expect(delete_buttons).to_have_count(2)
            # pdfs are by default sorted from newest to oldest
            expect(self.page.locator("#pdf-link-1")).to_contain_text("pdf_1_11")
            expect(self.page.locator("#pdf-link-2")).to_contain_text("pdf_1_1")

    def test_sort(self):
        # we test if sorting works with most viewed
        pdf = self.user.profile.pdf_set.get(name='pdf_2_12')
        pdf.views = 1001
        pdf.save()

        pdf = self.user.profile.pdf_set.get(name='pdf_3_13')
        pdf.views = 101
        pdf.save()

        with sync_playwright() as p:
            self.open(f"{reverse('pdf_overview')}?sort=most_viewed", p)

            expect(self.page.locator("#pdf-link-1")).to_have_text("pdf_2_12")
            expect(self.page.locator("#pdf-link-2")).to_have_text("pdf_3_13")

    def test_delete(self):
        with sync_playwright() as p:
            # only display one pdf
            self.open(f"{reverse('pdf_overview')}?q=pdf_2_1", p)

            expect(self.page.locator("body")).to_contain_text("pdf_2_1")
            self.page.get_by_role("button", name="Delete").click()
            self.page.get_by_text("Confirm").click()

            # now there should be no PDFs matching the search criteria
            expect(self.page.locator("body")).to_contain_text("There aren't any PDFs matching the search criteria")

    def test_chancel_delete(self):
        with sync_playwright() as p:
            # only display one pdf
            self.open(f"{reverse('pdf_overview')}?q=pdf_2_1", p)

            expect(self.page.get_by_text("Confirm")).not_to_be_visible()
            expect(self.page.get_by_role("button", name="Cancel")).not_to_be_visible()
            expect(self.page.get_by_role("button", name="Delete")).to_be_visible()
            self.page.get_by_role("button", name="Delete").click()
            expect(self.page.get_by_text("Confirm")).to_be_visible()
            expect(self.page.get_by_role("button", name="Cancel")).to_be_visible()
            expect(self.page.get_by_role("button", name="Delete")).not_to_be_visible()
            self.page.get_by_role("button", name="Cancel").click()
            expect(self.page.get_by_text("Confirm")).not_to_be_visible()
            expect(self.page.get_by_role("button", name="Cancel")).not_to_be_visible()
            expect(self.page.get_by_role("button", name="Delete")).to_be_visible()

    def test_details(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')
        pdf.views = 1001
        pdf.save()

        # only check for date, time is not easily reproducible
        creation_date = pdf.creation_date.strftime('%B %d, %Y')

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'pdf_id': pdf.id}), p)

            expect(self.page.locator("content")).to_contain_text("pdf_1_1")
            expect(self.page.locator("#name")).to_contain_text("pdf_1_1")
            expect(self.page.locator("#description")).to_contain_text("this is number 1")
            expect(self.page.locator("#tags")).to_contain_text("#tag")
            expect(self.page.locator("content")).to_contain_text("1001")
            expect(self.page.locator("content")).to_contain_text(creation_date)

    def test_change_details(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'pdf_id': pdf.id}), p)

            self.page.locator("#name-edit").click()
            self.page.locator("#id_name").dblclick()
            self.page.locator("#id_name").fill("other name")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("content")).to_contain_text("other name")
            expect(self.page.locator("#name")).to_contain_text("other name")
            self.page.locator("#description-edit").click()
            self.page.get_by_text("this is number").click()
            self.page.get_by_text("this is number").fill("other description")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#description")).to_contain_text("other description")
            self.page.locator("#tags-edit").click()
            self.page.locator("#id_tag_string").click()
            self.page.locator("#id_tag_string").fill("other")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#tags")).to_contain_text("#other")

    def test_cancel_change_details(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'pdf_id': pdf.id}), p)

            for edit_name in ['#name-edit', '#description-edit', '#tags-edit']:
                expect(self.page.locator(edit_name)).to_contain_text("Edit")
                self.page.locator(edit_name).click()
                expect(self.page.locator(edit_name)).to_contain_text("Cancel")
                self.page.get_by_role("link", name="Cancel").click()
                expect(self.page.locator(edit_name)).to_contain_text("Edit")