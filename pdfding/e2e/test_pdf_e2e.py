from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from helpers import PdfDingE2ETestCase, cancel_delete_helper
from pdf.models import Pdf, Tag
from playwright.sync_api import expect, sync_playwright
from users.models import Profile


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
            self.page.locator("#add_pdf").click()
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
            expect(self.page.locator("body")).to_contain_text("now")

            # check tag sidebar
            for tag in ["1", "banana", "bread", "tag_0", "tag_1"]:
                expect(self.page.locator(f"#tag-{tag}")).to_contain_text(tag)

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
            self.open(reverse('add_pdf'), p)
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
            expect(self.page.locator("body")).to_contain_text("now")

        dummy_file_path.unlink()

    @patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_add_pdf_notes(self, mock_from_buffer):
        # this also tests the overview

        # just use some dummy file for uploading
        dummy_file_path = Path(__file__).parent / 'dummy.pdf'
        with open(dummy_file_path, 'w') as f:
            f.write('Some text')

        with sync_playwright() as p:
            self.open(reverse('add_pdf'), p)

            # assert notes field not visible at the beginning
            expect(self.page.locator("#notes")).not_to_be_visible()

            # add pdf and open notes field
            self.page.get_by_label("Use File Name:").check()
            self.page.locator("#id_file").click()
            self.page.locator("#id_file").set_input_files(dummy_file_path)
            self.page.locator("#show_notes").click()
            expect(self.page.locator("#notes")).to_be_visible()
            self.page.get_by_placeholder("Add Notes").click()
            self.page.get_by_placeholder("Add Notes").fill("some note")

            # assert collapsing notes field is working
            self.page.locator("#show_notes").click()
            expect(self.page.locator("#notes")).not_to_be_visible()

            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("body")).to_contain_text("dummy")
            expect(self.page.locator("#show-notes-1")).to_be_visible()

        dummy_file_path.unlink()

    @override_settings(DEMO_MODE=True)
    def test_add_pdf_demo_mode(self):
        with sync_playwright() as p:
            self.open(reverse('add_pdf'), p)
            self.page.get_by_label("Use File Name:").check()
            self.page.get_by_placeholder("Add Description").click()
            self.page.get_by_placeholder("Add Description").fill("Some Description")
            self.page.get_by_placeholder("Add Tags").click()
            self.page.get_by_placeholder("Add Tags").fill("bread tag_1 banana tag_0 1")
            expect(self.page.locator("#id_file")).not_to_be_visible()
            self.page.get_by_role("button", name="Submit").click()

            expect(self.page.locator("body")).to_contain_text("demo")
            expect(self.page.locator("body")).to_contain_text("#1 #banana #bread #tag_0 #tag_1")
            expect(self.page.locator("body")).to_contain_text("Some Description")
            expect(self.page.locator("body")).to_contain_text("now")

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
            self.page.locator("#add_pdf").click()
            self.page.get_by_role("link", name="Bulk").click()
            self.page.locator("#id_file").click()
            self.page.locator("#id_file").set_input_files(dummy_file_paths)
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
            expect(self.page.locator("body")).to_contain_text("now")

            # check tag sidebar
            for tag in ["1", "banana", "bread", "tag_0", "tag_1"]:
                expect(self.page.locator(f"#tag-{tag}")).to_contain_text(tag)

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

    @patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_bulk_add_notes(self, mock_from_buffer):
        # just use some dummy file for uploading
        dummy_file_path = Path(__file__).parent / 'dummy.pdf'
        with open(dummy_file_path, 'w') as f:
            f.write('Some text')

        with sync_playwright() as p:
            self.open(reverse('bulk_add_pdfs'), p)

            # assert notes field not visible at the beginning
            expect(self.page.locator("#notes")).not_to_be_visible()

            # add pdf and open notes field
            self.page.locator("#id_file").click()
            self.page.locator("#id_file").set_input_files([dummy_file_path])

            self.page.locator("#show_notes").click()
            expect(self.page.locator("#notes")).to_be_visible()
            self.page.get_by_placeholder("Add Notes").click()
            self.page.get_by_placeholder("Add Notes").fill("some note")

            # assert collapsing notes field is working
            self.page.locator("#show_notes").click()
            expect(self.page.locator("#notes")).not_to_be_visible()

            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("body")).to_contain_text("dummy")
            expect(self.page.locator("#show-notes-1")).to_be_visible()

        dummy_file_path.unlink()

    @override_settings(DEMO_MODE=True)
    def test_bulk_add_pdf_demo(self):
        with sync_playwright() as p:
            self.open(reverse('bulk_add_pdfs'), p)
            self.page.get_by_placeholder("Add Description").click()
            self.page.get_by_placeholder("Add Description").fill("Some Description")
            self.page.get_by_placeholder("Add Tags").click()
            self.page.get_by_placeholder("Add Tags").fill("bread tag_1 banana tag_0 1")
            expect(self.page.locator("#id_file")).not_to_be_visible()
            self.page.get_by_role("button", name="Submit").click()

            # check center
            expect(self.page.locator("body")).to_contain_text("demo")
            expect(self.page.locator("body")).to_contain_text("#1 #banana #bread #tag_0 #tag_1")
            expect(self.page.locator("body")).to_contain_text("Some Description")
            expect(self.page.locator("body")).to_contain_text("now")

            # check tag sidebar
            for tag in ["1", "banana", "bread", "tag_0", "tag_1"]:
                expect(self.page.locator(f"#tag-{tag}")).to_contain_text(tag)

            # check sidebar links
            # first tag starting with character
            expect(self.page.get_by_role("link", name="1", exact=True)).to_have_attribute(
                "href", "/pdf/query/?search=%231"
            )
            # non first tag starting with character
            expect(self.page.get_by_role("link", name="bread", exact=True)).to_have_attribute(
                "href", "/pdf/query/?search=%23bread"
            )


class PdfOverviewE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()

        tag = Tag.objects.create(name='tag', owner=self.user.profile)

        # create some pdfs
        for i in range(1, 15):
            pdf = Pdf.objects.create(
                owner=self.user.profile, name=f'pdf_{i % 5}_{i}', description=f'this is number {i}'
            )

            # add a tag to pdf 1, 6
            if i % 5 == 1:
                pdf.tags.set([tag])

    # def test_thumbnails_on(self):
    #     self.user.profile.show_thumbnails = 'Enabled'
    #     self.user.profile.save()
    #
    #     with sync_playwright() as p:
    #         self.open(reverse('pdf_overview'), p)
    #         expect(self.page.locator("#thumbnail-1")).to_be_visible()
    #
    # def test_thumbnail_preview(self):
    #     self.user.profile.show_thumbnails = 'Enabled'
    #     self.user.profile.save()
    #
    #     with sync_playwright() as p:
    #         self.open(reverse('pdf_overview'), p)
    #
    #         expect(self.page.locator("#preview_inner")).not_to_be_visible()
    #         self.page.locator("#thumbnail-1").click()
    #         expect(self.page.locator("#preview_inner")).to_be_visible()
    #
    #         # click somewhere
    #         self.page.get_by_role("banner").click()
    #         expect(self.page.locator("#preview_inner")).not_to_be_visible()
    #
    # def test_thumbnails_off(self):
    #     self.user.profile.show_thumbnails = 'Disabled'
    #     self.user.profile.save()
    #
    #     with sync_playwright() as p:
    #         self.open(reverse('pdf_overview'), p)
    #         expect(self.page.locator("#thumbnail-1")).not_to_be_visible()

    def test_notes(self):
        pdf = Pdf.objects.get(name='pdf_4_14')
        pdf.notes = 'some markdown notes'
        pdf.save()

        with sync_playwright() as p:
            self.open(f"{reverse('pdf_overview')}?search=pdf_4_14", p)
            expect(self.page.locator("#show-notes-1")).to_be_visible()
            expect(self.page.locator("#notes-1")).not_to_be_visible()
            self.page.locator("#show-notes-1").click()
            expect(self.page.locator("#notes-1")).to_be_visible()
            expect(self.page.locator("#notes-1")).to_contain_text("some markdown notes")
            self.page.locator("#show-notes-1").click()
            expect(self.page.locator("#notes-1")).not_to_be_visible()

    def test_no_notes(self):
        pdf = Pdf.objects.get(name='pdf_4_14')
        pdf.notes = ''
        pdf.save()

        with sync_playwright() as p:
            self.open(f"{reverse('pdf_overview')}?search=pdf_4_14", p)
            expect(self.page.locator("#show-notes-1")).not_to_be_visible()

    def test_star(self):
        with sync_playwright() as p:
            self.open(f"{reverse('pdf_overview')}?search=pdf_4_14", p)

            expect(self.page.locator("#starred-icon-1")).not_to_be_visible()
            self.page.locator("#open-actions-1").click()
            expect(self.page.locator("#star-1")).to_contain_text("Star")
            self.page.locator("#star-1").click()
            expect(self.page.locator("#starred-icon-1")).to_be_visible()
            self.page.locator("#open-actions-1").click()
            expect(self.page.locator("#star-1")).to_contain_text("Unstar")
            self.page.locator("#star-1").click()
            expect(self.page.locator("#starred-icon-1")).not_to_be_visible()
            self.page.locator("#open-actions-1").click()
            expect(self.page.locator("#star-1")).to_contain_text("Star")

    @staticmethod
    def new_fuzzy_filter_pdfs(pdfs, search):
        filtered_pdfs = pdfs.filter(name__icontains=search)

        return filtered_pdfs

    @patch('pdf.views.pdf_views.OverviewMixin.fuzzy_filter_pdfs', new=new_fuzzy_filter_pdfs)
    def test_archive(self):
        with sync_playwright() as p:
            self.open(f"{reverse('pdf_overview')}?search=pdf_4_14", p)

            expect(self.page.locator("#pdf-link-1")).to_be_visible()
            self.page.locator("#open-actions-1").click()
            self.page.locator("#archive-1").click()
            expect(self.page.locator("#pdf-link-1")).not_to_be_visible()

            self.open(f"{reverse('pdf_overview')}?selection=archived", p)
            expect(self.page.locator("#pdf-link-1")).to_be_visible()
            expect(self.page.locator("#pdf-link-1")).to_contain_text("pdf_4_14")

    def test_progress_bar_off_number_pages(self):
        pdf = Pdf.objects.get(name='pdf_1_1')
        pdf.number_of_pages = -1
        pdf.save()

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("#progressbar-1")).not_to_be_visible()

    def test_preview(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#preview_inner")).not_to_be_visible()
            self.page.locator("#open-actions-1").click()
            self.page.locator("#preview-1").click()
            expect(self.page.locator("#preview_inner")).to_be_visible()

            # click somewhere
            self.page.get_by_role("banner").click()
            expect(self.page.locator("#preview_inner")).not_to_be_visible()

    def test_search_tags(self):
        with sync_playwright() as p:
            # trigger search by clicking on sidebar
            # display the three pdfs with the tag 'tag'
            self.open(reverse('pdf_overview'), p)
            self.page.get_by_role("link", name="#tag").first.click()

            # assert there are three pdfs matching the search
            # pdfs are by default sorted from newest to oldest
            expect(self.page.locator("#pdf-link-1")).to_contain_text("pdf_1_11")
            expect(self.page.locator("#pdf-link-2")).to_contain_text("pdf_1_6")
            expect(self.page.locator("#pdf-link-3")).to_contain_text("pdf_1_1")
            expect(self.page.locator("#pdf-link-4")).not_to_be_visible()
            expect(self.page.locator("#pdf-link-1")).to_contain_text("pdf_1_11")
            expect(self.page.locator("#pdf-link-2")).to_contain_text("pdf_1_6")
            expect(self.page.locator("#pdf-link-3")).to_contain_text("pdf_1_1")

    @patch('pdf.views.pdf_views.OverviewMixin.fuzzy_filter_pdfs', new=new_fuzzy_filter_pdfs)
    def test_search_names(self):
        with sync_playwright() as p:
            # display the three pdfs with the tag 'tag'
            self.open(f"{reverse('pdf_overview')}?search=pdf_2_", p)

            # assert there are three pdfs matching the search
            # pdfs are by default sorted from newest to oldest
            expect(self.page.locator("#pdf-link-1")).to_contain_text("pdf_2_12")
            expect(self.page.locator("#pdf-link-2")).to_contain_text("pdf_2_7")
            expect(self.page.locator("#pdf-link-3")).to_contain_text("pdf_2_2")
            expect(self.page.locator("#pdf-link-4")).not_to_be_visible()

    @patch('pdf.views.pdf_views.OverviewMixin.fuzzy_filter_pdfs', new=new_fuzzy_filter_pdfs)
    def test_search_names_and_tags(self):
        with sync_playwright() as p:
            # display the three pdfs with the tag 'tag'
            self.open(f"{reverse('pdf_overview')}?search=pdf_1_1&tags=tag", p)

            # assert there are three pdfs matching the search
            # pdfs are by default sorted from newest to oldest
            expect(self.page.locator("#pdf-link-1")).to_contain_text("pdf_1_11")
            expect(self.page.locator("#pdf-link-2")).to_contain_text("pdf_1_1")
            expect(self.page.locator("#pdf-link-3")).not_to_be_visible()

    def test_search_filters(self):
        with sync_playwright() as p:
            self.open(f"{reverse('pdf_overview')}?search=pdf_1_1&tags=tag", p)

            # check that filters have the correct text and are visible
            expect(self.page.locator("#search_filter")).to_contain_text("pdf_1_1")
            expect(self.page.locator("#tag_tag_filter")).to_contain_text("#tag")
            expect(self.page.locator("#search_filter")).to_be_visible()
            expect(self.page.locator("#tag_tag_filter")).to_be_visible()

            # check that filters are invisible
            self.page.locator("#search_filter").get_by_role("img").click()
            self.page.locator("#tag_tag_filter").get_by_role("img").click()
            expect(self.page.locator("#search_filter")).not_to_be_visible()
            expect(self.page.locator("#tag_tag_filter")).not_to_be_visible()

    def test_sort(self):
        self.user.profile.pdf_sorting = Profile.PdfSortingChoice.MOST_VIEWED
        self.user.profile.save()

        # we test if sorting works with most viewed
        pdf = self.user.profile.pdf_set.get(name='pdf_2_12')
        pdf.views = 1001
        pdf.save()

        pdf = self.user.profile.pdf_set.get(name='pdf_3_13')
        pdf.views = 101
        pdf.save()

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#pdf-link-1")).to_have_text("pdf_2_12")
            expect(self.page.locator("#pdf-link-2")).to_have_text("pdf_3_13")

    def test_change_sorting(self):
        self.assertEqual(self.user.profile.pdf_sorting, Profile.PdfSortingChoice.NEWEST)

        with sync_playwright() as p:
            self.open(reverse("pdf_overview"), p)

            self.page.locator("#sorting_settings").click()
            self.page.get_by_text("A - Z").click()

        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.pdf_sorting, Profile.PdfSortingChoice.NAME_ASC)

    @patch('pdf.views.pdf_views.OverviewMixin.fuzzy_filter_pdfs', new=new_fuzzy_filter_pdfs)
    def test_delete(self):
        with sync_playwright() as p:
            # only display one pdf
            self.open(f"{reverse('pdf_overview')}?search=pdf_2_1", p)

            expect(self.page.locator("body")).to_contain_text("pdf_2_1")
            self.page.locator("#open-actions-1").click()
            self.page.locator("#delete-1").click()
            self.page.get_by_role("button", name="Submit").click()

            # now there should be no PDFs matching the search criteria
            expect(self.page.locator("body")).to_contain_text("There aren't any PDFs matching the current filters")

    def test_cancel_delete(self):
        with sync_playwright() as p:
            # only display one pdf
            self.open(f"{reverse('pdf_overview')}?search=pdf_2_1", p)

            expect(self.page.locator("#delete_pdf_modal").first).not_to_be_visible()
            self.page.locator("#open-actions-1").click()
            self.page.locator("#delete-1").click()
            expect(self.page.locator("#delete_pdf_modal").first).to_be_visible()
            self.page.locator("#cancel_delete").get_by_text("Cancel").click()
            expect(self.page.locator("#delete_pdf_modal").first).not_to_be_visible()

    def test_sidebar_tags_normal_mode(self):
        profile = self.user.profile
        profile.tags_tree_mode = 'Disabled'
        profile.save()

        tags = []
        tag_names = ['hobbies/sports', 'programming/python/django', 'other']

        for tag_name in tag_names:
            tag = Tag.objects.create(name=tag_name, owner=self.user.profile)
            tags.append(tag)

        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')
        pdf.tags.set(tags)

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            # playwright has problems parsing "/" in locators
            playwright_tag_names = ['hobbies\\/sports', 'programming\\/python\\/django', 'other']

            for playwright_tag_name, tag_name in zip(playwright_tag_names, tag_names):
                expect(self.page.locator(f"#tag-{playwright_tag_name}")).to_contain_text(tag_name)
                expect(self.page.locator(f"#tag-{playwright_tag_name}")).to_be_visible()

            # no tags were created with parent names, so they should not exist
            for tag_name in ['hobbies', 'programming\\/python']:
                expect(self.page.locator(f"#tag-{tag_name}")).not_to_be_visible()

    def test_sidebar_tags_tree_mode(self):
        profile = self.user.profile
        profile.tags_tree_mode = 'Enabled'
        profile.save()

        tags = []
        # we use 1_programming as previously tags starting with a number did not work
        tag_names = ['1_programming/python/django', 'other']

        for tag_name in tag_names:
            tag = Tag.objects.create(name=tag_name, owner=self.user.profile)
            tags.append(tag)

        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')
        pdf.tags.set(tags)

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            for tag_name in ['1_programming', 'other']:
                expect(self.page.locator(f"#tag-{tag_name}")).to_contain_text(tag_name)
                expect(self.page.locator(f"#tag-{tag_name}")).to_be_visible()

            # children not open so they should not be visible
            for tag_name in ['1_programming\\/python', '1_programming\\/python\\/django']:
                expect(self.page.locator(f"#tag-{tag_name}")).not_to_be_visible()

            # only 1_programming should have open button
            expect(self.page.locator("#open-children-1_programming")).to_be_visible()
            expect(self.page.locator("#open-children-other")).not_to_be_visible()

            # click open 1_programming
            self.page.locator("#open-children-1_programming").click()
            expect(self.page.locator("#tag-1_programming\\/python")).to_be_visible()
            expect(self.page.locator("#tag-1_programming\\/python\\/django")).not_to_be_visible()

            # click open programming/python
            self.page.locator("#open-children-1_programming\\/python").click()
            expect(self.page.locator("#tag-1_programming\\/python\\/django")).to_be_visible()

            # click close programming
            self.page.locator("#open-children-1_programming").click()
            expect(self.page.locator("#tag-1_programming\\/python")).not_to_be_visible()
            expect(self.page.locator("#tag-1_programming\\/python\\/django")).not_to_be_visible()


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
            expect(self.page.locator("#notes")).to_contain_text("some notes")
            expect(self.page.locator("#tags")).to_contain_text("#tag")
            expect(self.page.locator("#progress")).to_contain_text("10% - Page 1 of 10")
            expect(self.page.locator("#views")).to_contain_text("1001")
            expect(self.page.locator("#creation_date")).to_contain_text(creation_date)
            expect(self.page.locator("#pdf_id")).to_contain_text(str(pdf.id))

    def test_details_progress_not_visible(self):
        pdf = self.user.profile.pdf_set.get(name='pdf_1_1')
        pdf.views = 1001
        pdf.number_of_pages = -1
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
            expect(self.page.locator("#progress")).not_to_be_visible()
            expect(self.page.locator("content")).to_contain_text("1001")
            expect(self.page.locator("content")).to_contain_text(creation_date)

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
        self.tag = Tag.objects.create(name='bla', owner=self.user.profile)
        pdf.tags.set([self.tag])

    def test_delete_tag_cancel(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            self.page.locator("#tag-bla").get_by_role("img").click()
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
            self.page.locator("#tag-bla").get_by_role("img").click()
            expect(self.page.locator("#delete-tag-bla")).to_be_visible()

            # click somewhere
            self.page.get_by_role("banner").click()

            # tag options should be closed now
            expect(self.page.locator("#delete-tag-bla")).not_to_be_visible()

    def test_delete_tag_normal_mode(self):
        profile = self.user.profile
        profile.tags_tree_mode = 'Disabled'
        profile.save()

        tag_2 = Tag.objects.create(name=f'{self.tag.name}/child', owner=self.user.profile)

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#tag-bla")).to_contain_text('bla')
            expect(self.page.locator("body")).to_contain_text("#bla")
            self.page.locator("#tag-bla").get_by_role("img").click()
            self.page.locator("#delete-tag-bla").get_by_text("Delete").click()
            self.page.locator("#confirm-delete-tag-bla").click()
            expect(self.page.locator("#tag-bla")).not_to_be_visible()
            expect(self.page.locator("body")).not_to_contain_text("#bla")

        self.assertFalse(self.user.profile.tag_set.filter(id=self.tag.id).exists())
        self.assertTrue(self.user.profile.tag_set.filter(id=tag_2.id).exists())

    def test_delete_tag_tree_mode(self):
        profile = self.user.profile
        profile.tags_tree_mode = 'Enabled'
        profile.save()

        tag_2 = Tag.objects.create(name=f'{self.tag.name}/child', owner=self.user.profile)

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#tag-bla")).to_contain_text('bla')
            expect(self.page.locator("body")).to_contain_text("#bla")
            self.page.locator("#tag-bla").get_by_role("img").click()
            self.page.locator("#delete-tag-bla").get_by_text("Delete").click()
            self.page.locator("#confirm-delete-tag-bla").click()
            expect(self.page.locator("#tag-bla")).not_to_be_visible()
            expect(self.page.locator("body")).not_to_contain_text("#bla")
            expect(self.page.locator("#tag-bla\\/child")).not_to_be_visible()
            expect(self.page.locator("body")).not_to_contain_text("#bla/child")

        self.assertFalse(self.user.profile.tag_set.filter(id=self.tag.id).exists())
        self.assertFalse(self.user.profile.tag_set.filter(id=tag_2.id).exists())

    def test_rename_tag_click_away(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#tag_rename_form")).not_to_be_visible()
            self.page.locator("#tag-bla").get_by_role("img").click()
            self.page.locator("#rename-tag-bla").get_by_text("Rename").click()
            expect(self.page.locator("#tag_rename_form")).to_be_visible()

            # click somewhere
            self.page.get_by_role("banner").click()

            # tag rename should be closed now
            expect(self.page.locator("#tag_rename_form")).not_to_be_visible()

    def test_rename_tag_cancel(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#tag_rename_form")).not_to_be_visible()
            self.page.locator("#tag-bla").get_by_role("img").click()
            self.page.locator("#rename-tag-bla").get_by_text("Rename").click()
            expect(self.page.locator("#tag_rename_form")).to_be_visible()

            # click cancel
            self.page.locator("#tag_rename_form").get_by_text("Cancel").click()

            # tag rename should be closed now
            expect(self.page.locator("#tag_rename_form")).not_to_be_visible()

    def test_rename_tag_normal_mode(self):
        profile = self.user.profile
        profile.tags_tree_mode = 'Disabled'
        profile.save()

        tag_2 = Tag.objects.create(name=f'{self.tag.name}/child', owner=self.user.profile)

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#tag-bla")).to_contain_text('bla')
            expect(self.page.locator("body")).to_contain_text("#bla")
            expect(self.page.locator("body")).not_to_contain_text("#renamed")

            self.page.locator("#tag-bla").get_by_role("img").click()
            self.page.locator("#rename-tag-bla").get_by_text("Rename").click()

            self.page.locator("#id_name").dblclick()
            self.page.locator("#id_name").fill("renamed")
            self.page.get_by_role("button", name="Submit").click()

            expect(self.page.locator("#tag-bla")).not_to_be_visible()
            expect(self.page.locator("#tag-renamed")).to_be_visible()
            expect(self.page.locator("#tag-renamed")).to_contain_text('renamed')
            expect(self.page.locator("body")).to_contain_text("#renamed")
            expect(self.page.locator("body")).not_to_contain_text("#bla")

        self.assertEqual(self.user.profile.tag_set.filter(id=self.tag.id).first().name, 'renamed')
        self.assertEqual(self.user.profile.tag_set.filter(id=tag_2.id).first().name, tag_2.name)

    def test_rename_tag_tree_mode(self):
        profile = self.user.profile
        profile.tags_tree_mode = 'Enabled'
        profile.save()

        tag_2 = Tag.objects.create(name=f'{self.tag.name}/child', owner=self.user.profile)

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#tag-bla")).to_contain_text('bla')
            expect(self.page.locator("body")).to_contain_text("#bla")
            expect(self.page.locator("body")).not_to_contain_text("#renamed")

            self.page.locator("#tag-bla").get_by_role("img").click()
            self.page.locator("#rename-tag-bla").get_by_text("Rename").click()

            self.page.locator("#id_name").dblclick()
            self.page.locator("#id_name").fill("renamed")
            self.page.get_by_role("button", name="Submit").click()

            expect(self.page.locator("#tag-bla")).not_to_be_visible()
            expect(self.page.locator("#tag-renamed")).to_be_visible()
            expect(self.page.locator("#tag-renamed")).to_contain_text('renamed')
            expect(self.page.locator("body")).to_contain_text("#renamed")
            expect(self.page.locator("body")).not_to_contain_text("#bla")

        self.assertEqual(self.user.profile.tag_set.filter(id=self.tag.id).first().name, 'renamed')
        self.assertEqual(self.user.profile.tag_set.filter(id=tag_2.id).first().name, 'renamed/child')
