from datetime import datetime, timedelta, timezone

from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models.pdf_models import Pdf, Tag
from pdf.services.pdf_services import get_or_create_pdf_reading_info
from playwright.sync_api import expect, sync_playwright


class TestCoreE2ETestCase(PdfDingE2ETestCase):
    def test_dashboard(self):
        collection = self.user.profile.current_collection
        pdf_1 = Pdf.objects.create(name='some_pdf', collection=collection)
        pdf_2 = Pdf.objects.create(name='other_pdf', collection=collection)
        Pdf.objects.create(name='further_pdf', collection=collection)
        tag = Tag.objects.create(name='some_tag', workspace=self.user.profile.current_workspace)
        pdf_1.tags.set([tag])

        # make pdf 0 the most recently viewed pdf
        reading_info = get_or_create_pdf_reading_info(pdf_1, self.user.profile)
        reading_info.last_viewed_date = datetime.now(timezone.utc) + timedelta(minutes=2)
        reading_info.save()
        reading_info = get_or_create_pdf_reading_info(pdf_2, self.user.profile)
        reading_info.last_viewed_date = datetime.now(timezone.utc) + timedelta(minutes=1)
        reading_info.save()

        with sync_playwright() as p:
            self.open(reverse('home'), p)

            # check recently viewed pdfs, pdf_3 was not viewed yet
            expect(self.page.locator("#recently-viewed-1")).to_contain_text("some_pdf")
            expect(self.page.locator("#recently-viewed-1")).to_contain_text("some_tag")
            expect(self.page.locator("#recently-viewed-2")).to_contain_text("other_pdf")
            expect(self.page.locator("#recently-viewed-3")).not_to_be_visible()

            # check recently added pdfs
            expect(self.page.locator("#recently-added-1")).to_contain_text("further_pdf")
            expect(self.page.locator("#recently-added-2")).to_contain_text("other_pdf")
            expect(self.page.locator("#recently-added-3")).to_contain_text("some_pdf")
            expect(self.page.locator("#recently-added-3")).to_contain_text("some_tag")

            # check statistics
            expect(self.page.locator("#pdfs-stats")).to_contain_text("3")
            expect(self.page.locator("#collections-stats")).to_contain_text("1")
            expect(self.page.locator("#tags-stats")).to_contain_text("1")
            expect(self.page.locator("#users-stats")).to_contain_text("1")
            expect(self.page.locator("#shared-pdfs-stats")).to_contain_text("0")
            expect(self.page.locator("#shared-collections-stats")).to_contain_text("0")
            expect(self.page.locator("#total-pdf-size-stats")).to_contain_text("0 KB")
