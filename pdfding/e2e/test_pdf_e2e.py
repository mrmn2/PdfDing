from pathlib import Path
from unittest.mock import patch

from django.urls import reverse
from helpers import PdfDingE2ETestCase, cancel_delete_helper
from pdf.models import Pdf, Tag
from playwright.sync_api import expect, sync_playwright


class NoPdfE2ETestCase(PdfDingE2ETestCase):
    def test_pdf_overview_no_pdfs(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("body")).to_contain_text("You have no PDFs yet")
            expect(self.page.locator("body")).to_contain_text("Get started by adding PDFs.")

    @patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_add_pdf_specify_name(self, mock_from_buffer):
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
            self.page.locator("#id_file").click()
            self.page.locator("#id_file").set_input_files(dummy_file_path)
            self.page.get_by_placeholder("Add Tags").click()
            self.page.get_by_placeholder("Add Tags").fill("bread tag_1 banana tag_0 1")
            self.page.get_by_role("button", name="Submit").click()

            # check center
            expect(self.page.locator("body")).to_contain_text("Some Name")
            expect(self.page.locator("body")).to_contain_text("#1 #banana #bread #tag_0 #tag_1")
            expect(self.page.locator("body")).to_contain_text("Some Description")
            expect(self.page.locator("body")).to_contain_text("now |")

            # check tag sidebar
            for i, tags in enumerate([["1"], ["banana", "bread"], ["tag_0", "tag_1"]]):
                for tag in tags:
                    expect(self.page.locator(f"#tags_{i}")).to_contain_text(tag)

            # check sidebar links
            # first tag starting with character
            expect(self.page.get_by_role("link", name="1", exact=True)).to_have_attribute(
                "href", "/pdf/query/?search=%231"
            )
            # non first tag starting with character
            expect(self.page.get_by_role("link", name="bread", exact=True)).to_have_attribute(
                "href", "/pdf/query/?search=%23bread"
            )

        dummy_file_path.unlink()

    @patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_add_pdf_use_file_name(self, mock_from_buffer):
        # this also tests the overview

        # just use some dummy file for uploading
        dummy_file_path = Path(__file__).parent / 'dummy.pdf'
        with open(dummy_file_path, 'w') as f:
            f.write('Some text')

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            self.page.get_by_role("link", name="Add PDF").click()
            self.page.get_by_label("Use File Name:").check()
            self.page.get_by_placeholder("Add Description").click()
            self.page.get_by_placeholder("Add Description").fill("Some Description")
            self.page.locator("#id_file").click()
            self.page.locator("#id_file").set_input_files(dummy_file_path)
            self.page.get_by_placeholder("Add Tags").click()
            self.page.get_by_placeholder("Add Tags").fill("bread tag_1 banana tag_0 1")
            self.page.get_by_role("button", name="Submit").click()

            expect(self.page.locator("body")).to_contain_text("dummy")
            expect(self.page.locator("body")).to_contain_text("#1 #banana #bread #tag_0 #tag_1")
            expect(self.page.locator("body")).to_contain_text("Some Description")
            expect(self.page.locator("body")).to_contain_text("now |")

        dummy_file_path.unlink()

    @patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_bulk_add_pdf(self, mock_from_buffer):
        # this also tests the overview

        # just use some dummy file for uploading
        dummy_file_paths = []

        for name in ['dummy_1.pdf', 'dummy_2.pdf']:
            dummy_file_path = Path(__file__).parent / name
            dummy_file_paths.append(dummy_file_path)
            with open(dummy_file_path, 'w') as f:
                f.write('Some text')

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            self.page.get_by_role("link", name="Add PDF").click()
            self.page.get_by_role("link", name="Bulk").click()
            self.page.get_by_label("File:").click()
            self.page.get_by_label("File:").set_input_files(dummy_file_paths)
            self.page.get_by_placeholder("Add Description").click()
            self.page.get_by_placeholder("Add Description").fill("Some Description")
            self.page.get_by_placeholder("Add Tags").click()
            self.page.get_by_placeholder("Add Tags").fill("bread tag_1 banana tag_0 1")
            self.page.get_by_role("button", name="Submit").click()

            # check center
            expect(self.page.locator("body")).to_contain_text("dummy_1")
            expect(self.page.locator("body")).to_contain_text("dummy_2")
            expect(self.page.locator("body")).to_contain_text("#1 #banana #bread #tag_0 #tag_1")
            expect(self.page.locator("body")).to_contain_text("Some Description")
            expect(self.page.locator("body")).to_contain_text("now |")

            # check tag sidebar
            for i, tags in enumerate([["1"], ["banana", "bread"], ["tag_0", "tag_1"]]):
                for tag in tags:
                    expect(self.page.locator(f"#tags_{i}")).to_contain_text(tag)

            # check sidebar links
            # first tag starting with character
            expect(self.page.get_by_role("link", name="1", exact=True)).to_have_attribute(
                "href", "/pdf/query/?search=%231"
            )
            # non first tag starting with character
            expect(self.page.get_by_role("link", name="bread", exact=True)).to_have_attribute(
                "href", "/pdf/query/?search=%23bread"
            )

        for path in dummy_file_paths:
            path.unlink()


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

    def test_progress_bar_on(self):
        # progress bars are shown by default

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("#progressbar-1")).to_be_visible()

    def test_progress_bar_off(self):
        self.user.profile.show_progress_bars = 'Disabled'
        self.user.profile.save()

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("#progressbar-1")).not_to_be_visible()

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
            self.page.locator("#delete-pdf-1").click()
            self.page.locator("#confirm-delete-pdf-1").click()

            # now there should be no PDFs matching the search criteria
            expect(self.page.locator("body")).to_contain_text("There aren't any PDFs matching the search criteria")

    def test_cancel_delete(self):
        with sync_playwright() as p:
            # only display one pdf
            self.open(f"{reverse('pdf_overview')}?q=pdf_2_1", p)

            expect(self.page.locator("#confirm-delete-pdf-1")).not_to_be_visible()
            expect(self.page.locator("#cancel-delete-pdf-1")).not_to_be_visible()
            expect(self.page.locator("#delete-pdf-1")).to_be_visible()
            self.page.locator("#delete-pdf-1").click()
            expect(self.page.locator("#confirm-delete-pdf-1")).to_be_visible()
            expect(self.page.locator("#cancel-delete-pdf-1")).to_be_visible()
            expect(self.page.locator("#delete-pdf-1")).not_to_be_visible()
            self.page.locator("#cancel-delete-pdf-1").click()
            expect(self.page.locator("#confirm-delete-pdf-1")).not_to_be_visible()
            expect(self.page.locator("#cancel-delete-pdf-1")).not_to_be_visible()
            expect(self.page.locator("#delete-pdf-1")).to_be_visible()

    def test_details(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')
        pdf.views = 1001
        pdf.save()

        # only check for date, time is not easily reproducible
        creation_date = pdf.creation_date.strftime('%b. %-d, %Y')
        # months that are not shortened do not need the dot
        if 'May' in creation_date or 'July' in creation_date or 'June' in creation_date:
            creation_date.replace('.', '')

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'identifier': pdf.id}), p)

            expect(self.page.locator("content")).to_contain_text("pdf_1_1")
            expect(self.page.locator("#name")).to_contain_text("pdf_1_1")
            expect(self.page.locator("#description")).to_contain_text("this is number 1")
            expect(self.page.locator("#tags")).to_contain_text("#tag")
            expect(self.page.locator("#progress")).to_contain_text("100% - Page 1 of 1")
            expect(self.page.locator("content")).to_contain_text("1001")
            expect(self.page.locator("content")).to_contain_text(creation_date)

    def test_change_details(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'identifier': pdf.id}), p)

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
            self.open(reverse('pdf_details', kwargs={'identifier': pdf.id}), p)

            for edit_name in ['#name-edit', '#description-edit', '#tags-edit']:
                expect(self.page.locator(edit_name)).to_contain_text("Edit")
                self.page.locator(edit_name).click()
                expect(self.page.locator(edit_name)).to_contain_text("Cancel")
                self.page.get_by_role("link", name="Cancel").click()
                expect(self.page.locator(edit_name)).to_contain_text("Edit")

    def test_details_delete(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'identifier': pdf.id}), p)

            expect(self.page.locator("body")).to_contain_text("pdf_1_1")
            self.page.get_by_role("button", name="Delete").click()
            self.page.get_by_text("Confirm").click()

            expect(self.page.locator("body")).not_to_have_text("pdf_1_1")

    def test_details_cancel_delete(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')

        with sync_playwright() as p:
            self.open(reverse('pdf_details', kwargs={'identifier': pdf.id}), p)

            cancel_delete_helper(self.page)


class TagE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()

        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')
        tag = Tag.objects.create(name='bla', owner=self.user.profile)
        pdf.tags.set([tag])

    def test_delete_tag_cancel(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            self.page.locator("#tag-bla > a").first.click()
            expect(self.page.locator("#confirm-delete-tag-bla")).not_to_be_visible()
            expect(self.page.locator("#cancel-delete-tag-bla")).not_to_be_visible()
            expect(self.page.locator("#delete-tag-bla")).to_be_visible()
            expect(self.page.locator("#rename-tag-bla")).to_be_visible()
            self.page.locator("#delete-tag-bla").get_by_text("Delete").click()
            expect(self.page.locator("#confirm-delete-tag-bla")).to_be_visible()
            expect(self.page.locator("#cancel-delete-tag-bla")).to_be_visible()
            expect(self.page.locator("#delete-tag-bla")).not_to_be_visible()
            expect(self.page.locator("#rename-tag-bla")).not_to_be_visible()
            self.page.locator("#cancel-delete-tag-bla").click()
            expect(self.page.locator("#confirm-delete-tag-bla")).not_to_be_visible()
            expect(self.page.locator("#cancel-delete-tag-bla")).not_to_be_visible()
            expect(self.page.locator("#delete-tag-bla")).to_be_visible()
            expect(self.page.locator("#rename-tag-bla")).to_be_visible()

    def test_delete_tag_click_away(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            self.page.locator("#tag-bla > a").first.click()
            expect(self.page.locator("#delete-tag-bla")).to_be_visible()

            # click somewhere
            self.page.locator("span").filter(has_text="PDFs").click()

            # tag options should be closed now
            expect(self.page.locator("#delete-tag-bla")).not_to_be_visible()

    def test_delete_tag(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#tags_0")).to_contain_text('bla')
            expect(self.page.locator("body")).to_contain_text("#bla")
            self.page.locator("#tag-bla > a").first.click()
            self.page.locator("#delete-tag-bla").get_by_text("Delete").click()
            self.page.locator("#confirm-delete-tag-bla").click()
            expect(self.page.locator("#tags_0")).not_to_be_visible()
            expect(self.page.locator("body")).not_to_contain_text("#bla")

    def test_rename_tag_click_away(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#tag_rename_form")).not_to_be_visible()
            self.page.locator("#tag-bla > a").first.click()
            self.page.locator("#rename-tag-bla").get_by_text("Rename").click()
            expect(self.page.locator("#tag_rename_form")).to_be_visible()

            # click somewhere
            self.page.locator("span").filter(has_text="PDFs").click()

            # tag rename should be closed now
            expect(self.page.locator("#tag_rename_form")).not_to_be_visible()

    def test_rename_tag_cancel(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#tag_rename_form")).not_to_be_visible()
            self.page.locator("#tag-bla > a").first.click()
            self.page.locator("#rename-tag-bla").get_by_text("Rename").click()
            expect(self.page.locator("#tag_rename_form")).to_be_visible()

            # click cancel
            self.page.locator("#tag_rename_form").get_by_text("Cancel").click()

            # tag rename should be closed now
            expect(self.page.locator("#tag_rename_form")).not_to_be_visible()

    def test_rename_tag(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#tags_0")).to_contain_text('bla')
            expect(self.page.locator("body")).to_contain_text("#bla")
            expect(self.page.locator("body")).not_to_contain_text("#renamed")

            self.page.locator("#tag-bla > a").first.click()
            self.page.locator("#rename-tag-bla").get_by_text("Rename").click()

            self.page.locator("#id_name").dblclick()
            self.page.locator("#id_name").fill("renamed")
            self.page.get_by_role("button", name="Submit").click()

            expect(self.page.locator("#tags_0")).not_to_contain_text('bla')
            expect(self.page.locator("#tags_0")).to_contain_text('renamed')
            expect(self.page.locator("body")).to_contain_text("#renamed")
            expect(self.page.locator("body")).not_to_contain_text("#bla")
