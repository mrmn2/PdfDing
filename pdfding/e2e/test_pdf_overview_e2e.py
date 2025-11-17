from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models.pdf_models import Pdf, Tag
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
            self.page.locator("#show_additional").click()
            expect(self.page.locator("#notes")).to_be_visible()
            self.page.get_by_placeholder("Add Notes").click()
            self.page.get_by_placeholder("Add Notes").fill("some note")

            # assert collapsing notes field is working
            self.page.locator("#show_additional").click()
            expect(self.page.locator("#notes")).not_to_be_visible()

            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("body")).to_contain_text("dummy")
            expect(self.page.locator("#show-notes-1")).to_be_visible()

        dummy_file_path.unlink()

    @patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_add_file_directory(self, mock_from_buffer):
        # just use some dummy file for uploading
        dummy_file_path = Path(__file__).parent / 'dummy.pdf'
        with open(dummy_file_path, 'w') as f:
            f.write('Some text')

        with sync_playwright() as p:
            self.open(reverse('add_pdf'), p)

            # assert notes field not visible at the beginning
            expect(self.page.locator("#file_directory")).not_to_be_visible()

            # add pdf and open notes field
            self.page.get_by_placeholder("Add PDF Name").click()
            self.page.get_by_placeholder("Add PDF Name").fill("some_random_name")
            self.page.locator("#id_file").click()
            self.page.locator("#id_file").set_input_files(dummy_file_path)
            self.page.locator("#show_additional").click()
            expect(self.page.locator("#file_directory")).to_be_visible()
            self.page.get_by_placeholder("Add File Directory").click()
            self.page.get_by_placeholder("Add File Directory").fill("some/dir")

            # assert collapsing notes field is working
            self.page.locator("#show_additional").click()
            expect(self.page.locator("#file_directory")).not_to_be_visible()

            self.page.get_by_role("button", name="Submit").click()

        pdf = Pdf.objects.get(name='some_random_name')
        self.assertEqual(pdf.file.name, f'{pdf.owner.user.id}/pdf/some/dir/{pdf.name}.pdf')

        dummy_file_path.unlink()
        pdf.delete()

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

            self.page.locator("#show_additional").click()
            expect(self.page.locator("#notes")).to_be_visible()
            self.page.get_by_placeholder("Add Notes").click()
            self.page.get_by_placeholder("Add Notes").fill("some note")

            # assert collapsing notes field is working
            self.page.locator("#show_additional").click()
            expect(self.page.locator("#notes")).not_to_be_visible()

            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("body")).to_contain_text("dummy")
            expect(self.page.locator("#show-notes-1")).to_be_visible()

        dummy_file_path.unlink()

    @patch('pdf.forms.magic.from_buffer', return_value='application/pdf')
    def test_bulk_add_file_directory(self, mock_from_buffer):
        # just use some dummy file for uploading
        dummy_file_path = Path(__file__).parent / 'dummy.pdf'
        with open(dummy_file_path, 'w') as f:
            f.write('Some text')

        with sync_playwright() as p:
            self.open(reverse('bulk_add_pdfs'), p)

            # assert notes field not visible at the beginning
            expect(self.page.locator("#file_directory")).not_to_be_visible()

            # add pdf and open notes field
            self.page.locator("#id_file").click()
            self.page.locator("#id_file").set_input_files([dummy_file_path])

            self.page.locator("#show_additional").click()
            expect(self.page.locator("#file_directory")).to_be_visible()
            self.page.get_by_placeholder("Add File Directory").click()
            self.page.get_by_placeholder("Add File Directory").fill("some/dir")

            # assert collapsing notes field is working
            self.page.locator("#show_additional").click()
            expect(self.page.locator("#file_directory")).not_to_be_visible()

            self.page.get_by_role("button", name="Submit").click()

        pdf = Pdf.objects.get(name='dummy')
        self.assertEqual(pdf.file.name, f'{pdf.owner.user.id}/pdf/some/dir/{pdf.name}.pdf')

        dummy_file_path.unlink()
        pdf.delete()

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

    def test_load_next_page(self):
        self.user.profile.pdf_sorting = Profile.PdfSortingChoice.OLDEST
        self.user.profile.save()

        # in set up 14 pdfs were already created
        # other should not be shown as we'll search for pdf
        Pdf.objects.create(owner=self.user.profile, name='other')
        Pdf.objects.create(owner=self.user.profile, name='pdf_page_2')

        with sync_playwright() as p:
            self.open(f"{reverse('pdf_overview')}?search=pdf", p)
            expect(self.page.locator("#pdf-12")).to_be_visible()
            expect(self.page.locator("#pdf-15")).not_to_be_visible()

            self.page.locator("#next_page_1_toggle").click()
            # since other is not visible #pdf-15 will contain pdf_page_2
            expect(self.page.locator("#pdf-15")).to_be_visible()
            expect(self.page.locator("#pdf-15")).to_contain_text('pdf_page_2')
            expect(self.page.locator("#next_page_2_toggle")).not_to_be_visible()

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
            self.page.locator("#search_filter_close").get_by_role("img").click()
            self.page.locator("#tag_tag_filter").get_by_role("img").click()
            expect(self.page.locator("#search_filter")).not_to_be_visible()
            expect(self.page.locator("#tag_tag_filter")).not_to_be_visible()

    def test_sort(self):
        self.user.profile.pdf_sorting = Profile.PdfSortingChoice.MOST_VIEWED
        self.user.profile.save()

        # we test if sorting works with most viewed
        pdf = self.user.profile.pdfs.get(name='pdf_2_12')
        pdf.views = 1001
        pdf.save()

        pdf = self.user.profile.pdfs.get(name='pdf_3_13')
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

    def test_change_layout(self):
        self.assertEqual(self.user.profile.layout, Profile.LayoutChoice.COMPACT)

        with sync_playwright() as p:
            self.open(reverse("pdf_overview"), p)

            self.page.locator("#layout_settings").click()
            self.page.get_by_text("Grid").click()

        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.layout, Profile.LayoutChoice.GRID)

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

    def test_progress_bar_off_number_pages(self):
        pdf = Pdf.objects.get(name='pdf_1_1')
        pdf.number_of_pages = -1
        pdf.save()

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("#progressbar-1")).not_to_be_visible()

    def test_progress_bar_on(self):
        pdf = Pdf.objects.get(name='pdf_4_14')
        pdf.number_of_pages = 1
        pdf.save()

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("#progressbar-1")).to_be_visible()

    def test_progress_bar_off_settings(self):
        pdf = Pdf.objects.get(name='pdf_4_14')
        pdf.number_of_pages = 1
        pdf.save()

        self.user.profile.show_progress_bars = 'Disabled'
        self.user.profile.save()

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("#progressbar-1")).not_to_be_visible()

    @override_settings(SUPPORTER_EDITION=False)
    def test_nagging_modal_needs_nagging(self):
        self.user.profile.last_time_nagged = datetime.now(tz=timezone.utc) - timedelta(weeks=9)
        self.user.profile.save()

        self.assertTrue(self.user.profile.needs_nagging)

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("#nagging")).to_be_visible()

            self.page.get_by_role("button", name="Leave me alone").click()
            expect(self.page.locator("#nagging")).not_to_be_visible()

        changed_user = User.objects.get(id=self.user.id)
        self.assertFalse(changed_user.profile.needs_nagging)

        with sync_playwright() as p:
            # test opening again
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("#nagging")).not_to_be_visible()

    @override_settings(SUPPORTER_EDITION=True)
    def test_nagging_modal_not_needs_nagging(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("#nagging")).not_to_be_visible()
