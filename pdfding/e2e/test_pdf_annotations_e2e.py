from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models import Pdf, PdfComment, PdfHighlight
from playwright.sync_api import expect, sync_playwright
from users.models import Profile


class HighlightOverviewE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()

        self.pdf_1 = Pdf.objects.create(owner=self.user.profile, name='some_pdf')
        self.pdf_2 = Pdf.objects.create(owner=self.user.profile, name='some_other_pdf')

    def test_highlight_overview(self):
        PdfHighlight.objects.create(
            text='highlight_old', page=1, creation_date=self.pdf_1.creation_date, pdf=self.pdf_1
        )
        PdfHighlight.objects.create(
            text='highlight_new', page=2, creation_date=self.pdf_2.creation_date + timedelta(minutes=5), pdf=self.pdf_2
        )

        with sync_playwright() as p:
            self.open(f"{reverse('pdf_highlight_overview')}", p)
            expect(self.page.locator("#annotation-1")).to_contain_text("some_other_pdf")
            expect(self.page.locator("#annotation-text-1")).to_contain_text("highlight_new")
            expect(self.page.locator("#annotation-2")).to_contain_text("some_pdf")
            expect(self.page.locator("#annotation-text-2")).to_contain_text("highlight_old")

    def test_load_next_page(self):
        self.user.profile.annotation_sorting = Profile.AnnotationsSortingChoice.OLDEST
        self.user.profile.save()

        for i in range(12):
            PdfHighlight.objects.create(
                text=f'highlight_{i}', page=i, creation_date=self.pdf_1.creation_date, pdf=self.pdf_1
            )

        PdfHighlight.objects.create(
            text='highlight_page_2',
            page=13,
            creation_date=self.pdf_1.creation_date + timedelta(minutes=5),
            pdf=self.pdf_1,
        )

        with sync_playwright() as p:
            self.open(reverse('pdf_highlight_overview'), p)
            expect(self.page.locator("#annotation-12")).to_be_visible()
            expect(self.page.locator("#annotation-13")).not_to_be_visible()

            self.page.locator("#next_page_1_toggle").click()
            # since other is not visible #annotation-13 will contain pdf_highlight_2
            expect(self.page.locator("#annotation-13")).to_be_visible()
            expect(self.page.locator("#annotation-text-13")).to_contain_text("highlight_page_2")
            expect(self.page.locator("#next_page_2_toggle")).not_to_be_visible()

    def test_sort(self):
        self.user.profile.annotation_sorting = Profile.AnnotationsSortingChoice.OLDEST
        self.user.profile.save()

        PdfHighlight.objects.create(
            text='highlight_old', page=1, creation_date=self.pdf_1.creation_date, pdf=self.pdf_1
        )
        PdfHighlight.objects.create(
            text='highlight_new', page=2, creation_date=self.pdf_2.creation_date + timedelta(minutes=5), pdf=self.pdf_2
        )

        with sync_playwright() as p:
            self.open(f"{reverse('pdf_highlight_overview')}", p)
            expect(self.page.locator("#annotation-1")).to_contain_text("some_pdf")
            expect(self.page.locator("#annotation-text-1")).to_contain_text("highlight_old")
            expect(self.page.locator("#annotation-2")).to_contain_text("some_other_pdf")
            expect(self.page.locator("#annotation-text-2")).to_contain_text("highlight_new")

    def test_change_sorting(self):
        self.assertEqual(self.user.profile.annotation_sorting, Profile.AnnotationsSortingChoice.NEWEST)

        with sync_playwright() as p:
            self.open(reverse("pdf_highlight_overview"), p)

            self.page.locator("#sorting_settings").click()
            self.page.get_by_text("Oldest").click()

        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.annotation_sorting, Profile.AnnotationsSortingChoice.OLDEST)


class CommentOverviewE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()

        self.pdf_1 = Pdf.objects.create(owner=self.user.profile, name='some_pdf')
        self.pdf_2 = Pdf.objects.create(owner=self.user.profile, name='some_other_pdf')

    def test_highlight_overview(self):
        PdfComment.objects.create(text='comment_old', page=1, creation_date=self.pdf_1.creation_date, pdf=self.pdf_1)
        PdfComment.objects.create(
            text='comment_new', page=2, creation_date=self.pdf_2.creation_date + timedelta(minutes=5), pdf=self.pdf_2
        )

        with sync_playwright() as p:
            self.open(f"{reverse('pdf_comment_overview')}", p)
            expect(self.page.locator("#annotation-1")).to_contain_text("some_other_pdf")
            expect(self.page.locator("#annotation-text-1")).to_contain_text("comment_new")
            expect(self.page.locator("#annotation-2")).to_contain_text("some_pdf")
            expect(self.page.locator("#annotation-text-2")).to_contain_text("comment_old")

    def test_load_next_page(self):
        self.user.profile.annotation_sorting = Profile.AnnotationsSortingChoice.OLDEST
        self.user.profile.save()

        for i in range(12):
            PdfComment.objects.create(
                text=f'comment_{i}', page=i, creation_date=self.pdf_1.creation_date, pdf=self.pdf_1
            )

        PdfComment.objects.create(
            text='comment_page_2',
            page=13,
            creation_date=self.pdf_1.creation_date + timedelta(minutes=5),
            pdf=self.pdf_1,
        )

        with sync_playwright() as p:
            self.open(reverse('pdf_comment_overview'), p)
            expect(self.page.locator("#annotation-12")).to_be_visible()
            expect(self.page.locator("#annotation-13")).not_to_be_visible()

            self.page.locator("#next_page_1_toggle").click()
            # since other is not visible #annotation-13 will contain comment_page_2
            expect(self.page.locator("#annotation-13")).to_be_visible()
            expect(self.page.locator("#annotation-text-13")).to_contain_text("comment_page_2")
            expect(self.page.locator("#next_page_2_toggle")).not_to_be_visible()

    def test_sort(self):
        self.user.profile.annotation_sorting = Profile.AnnotationsSortingChoice.OLDEST
        self.user.profile.save()

        PdfComment.objects.create(text='comment_old', page=1, creation_date=self.pdf_1.creation_date, pdf=self.pdf_1)
        PdfComment.objects.create(
            text='comment_new', page=2, creation_date=self.pdf_2.creation_date + timedelta(minutes=5), pdf=self.pdf_2
        )

        with sync_playwright() as p:
            self.open(f"{reverse('pdf_comment_overview')}", p)
            expect(self.page.locator("#annotation-1")).to_contain_text("some_pdf")
            expect(self.page.locator("#annotation-text-1")).to_contain_text("comment_old")
            expect(self.page.locator("#annotation-2")).to_contain_text("some_other_pdf")
            expect(self.page.locator("#annotation-text-2")).to_contain_text("comment_new")

    #
    def test_change_sorting(self):
        self.assertEqual(self.user.profile.annotation_sorting, Profile.AnnotationsSortingChoice.NEWEST)

        with sync_playwright() as p:
            self.open(reverse("pdf_comment_overview"), p)

            self.page.locator("#sorting_settings").click()
            self.page.get_by_text("Oldest").click()

        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.annotation_sorting, Profile.AnnotationsSortingChoice.OLDEST)
