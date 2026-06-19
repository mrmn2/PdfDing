from datetime import datetime, timedelta, timezone

from django.contrib.auth.models import User
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models.shared_models import SharedCollection
from playwright.sync_api import expect, sync_playwright
from users.models import Profile


class NoSharedPdfE2ETestCase(PdfDingE2ETestCase):
    def test_shared_pdf_overview_no_shared_pdfs(self):
        with sync_playwright() as p:
            self.open(reverse('shared_collection_overview'), p)
            expect(self.page.locator("body")).to_contain_text("You have not shared any collections yet")

    def test_share_collection(self):
        with sync_playwright() as p:
            self.open(reverse('collection_details', kwargs={'identifier': self.user.profile.current_collection_id}), p)
            self.page.get_by_role("link", name="Share").click()
            self.page.get_by_role("textbox", name="Name:").click()
            self.page.get_by_role("textbox", name="Name:").fill("some_shared_collection")
            self.page.get_by_role("textbox", name="Password:").click()
            self.page.get_by_role("textbox", name="Password:").fill("123")
            self.page.get_by_role("textbox", name="Deletion input:").click()
            self.page.get_by_role("textbox", name="Deletion input:").fill("1d0h22m")
            self.page.get_by_role("button", name="Submit").click()

            expect(self.page.locator("#shared-obj-link-1")).to_contain_text("some_shared_collection")
            expect(self.page.locator("#shared-obj-1")).to_contain_text("Default")
            expect(self.page.locator("#shared-obj-1")).to_contain_text("deletes in 1 day")


class SharedCollectionE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()
        self.collection = self.user.profile.current_collection

    def test_sort(self):
        self.user.profile.shared_pdf_sorting = Profile.SharedPdfSortingChoice.NAME_DESC
        self.user.profile.save()

        # create some shared pdfs
        for name in ['Some_share', 'another_share', 'this is a share', 'Collection is shared']:
            SharedCollection.objects.create(name=name, collection=self.collection)

        with sync_playwright() as p:
            self.open(reverse('shared_collection_overview'), p)

            expect(self.page.locator("#shared-obj-link-1")).to_have_text("this is a share")
            expect(self.page.locator("#shared-obj-link-2")).to_have_text("Some_share")
            expect(self.page.locator("#shared-obj-link-3")).to_have_text("Collection is shared")
            expect(self.page.locator("#shared-obj-link-4")).to_have_text("another_share")

    def test_change_sorting(self):
        self.assertEqual(self.user.profile.shared_pdf_sorting, Profile.SharedPdfSortingChoice.NEWEST)

        with sync_playwright() as p:
            self.open(reverse("shared_collection_overview"), p)

            self.page.locator("#sorting_settings").click()
            self.page.get_by_text("A - Z").click()

        changed_user = User.objects.get(id=self.user.id)

        self.assertEqual(changed_user.profile.shared_pdf_sorting, Profile.SharedPdfSortingChoice.NAME_ASC)

    def test_load_next_page(self):
        self.user.profile.shared_pdf_sorting = Profile.SharedPdfSortingChoice.OLDEST
        self.user.profile.save()

        for i in range(14):
            SharedCollection.objects.create(name=f'shared_{i}', collection=self.user.profile.current_collection)

        with sync_playwright() as p:
            self.open(reverse('shared_collection_overview'), p)
            expect(self.page.locator("#shared-obj-12")).to_be_visible()
            expect(self.page.locator("#shared-obj-13")).not_to_be_visible()

            self.page.locator("#next_page_1_toggle").click()
            expect(self.page.locator("#shared-obj-13")).to_be_visible()
            expect(self.page.locator("#shared-obj-13")).to_contain_text('shared_12')
            expect(self.page.locator("#next_page_2_toggle")).not_to_be_visible()

    def test_delete(self):
        SharedCollection.objects.create(name='some_shared_collection', collection=self.collection)

        with sync_playwright() as p:
            self.open(f"{reverse('shared_collection_overview')}", p)

            expect(self.page.locator("#shared-obj-link-1")).to_have_text("some_shared_collection")
            self.page.locator("#delete_1 a").filter(has_text="Delete").click()
            self.page.locator("#delete_1").get_by_text("Confirm").click()

            expect(self.page.locator("body")).to_contain_text("You have not shared any collections yet")

    def test_cancel_delete(self):
        SharedCollection.objects.create(name='some_shared_collection', collection=self.collection)

        with sync_playwright() as p:
            self.open(f"{reverse('shared_collection_overview')}", p)

            self.page.locator("#delete_1 a").filter(has_text="Delete").click()
            expect(self.page.locator("#delete_1").get_by_text("Cancel")).to_be_visible()
            expect(self.page.locator("#delete_1").get_by_text("Confirm")).to_be_visible()
            expect(self.page.locator("#delete_1 a").filter(has_text="Delete")).not_to_be_visible()
            self.page.locator("#delete_1").get_by_text("Cancel").click()
            expect(self.page.locator("#delete_1 a").filter(has_text="Delete")).to_be_visible()
            expect(self.page.locator("#delete_1 a").filter(has_text="Cancel")).not_to_be_visible()
            expect(self.page.locator("#delete_1").get_by_text("Confirm")).not_to_be_visible()

    def test_details(self):
        shared_collection = SharedCollection.objects.create(
            name='some_shared_collection',
            collection=self.collection,
            password='password',
            deletion_date=datetime.now(timezone.utc) + timedelta(days=1, minutes=5),
        )

        with sync_playwright() as p:
            self.open(reverse('shared_collection_details', kwargs={'identifier': shared_collection.id}), p)

            expect(self.page.locator("body")).to_contain_text("some_shared_collection")
            expect(self.page.locator("#name")).to_contain_text("some_shared_collection")
            expect(self.page.locator("#collection")).to_contain_text("Default")
            expect(self.page.locator("#password")).to_contain_text("***")
            expect(self.page.locator("#deletion_date")).to_contain_text("deletes in 1 day")

    def test_change_details(self):
        shared_collection = SharedCollection.objects.create(
            name='some_shared_collection',
            collection=self.collection,
            password='password',
            deletion_date=datetime.now(timezone.utc) + timedelta(days=1, minutes=5),
        )

        # also test changing from inactive to active
        with sync_playwright() as p:
            self.open(reverse('shared_collection_details', kwargs={'identifier': shared_collection.id}), p)

            self.page.locator("#name-edit").click()
            self.page.locator("#id_name").dblclick()
            self.page.locator("#id_name").fill("other name")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("body")).to_contain_text("other name")
            expect(self.page.locator("#name")).to_contain_text("other name")
            self.page.locator("#password-edit").click()
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#password")).to_contain_text("not set")
            self.page.locator("#deletion_date-edit").click()
            self.page.get_by_placeholder("e.g. 1d0h22m").click()
            self.page.get_by_placeholder("e.g. 1d0h22m").fill("0d0h5m")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#deletion_date")).to_contain_text("deletes in 4 minutes")

    def test_cancel_change_details(self):
        shared_collection = SharedCollection.objects.create(name='some_shared_collection', collection=self.collection)

        with sync_playwright() as p:
            self.open(reverse('shared_collection_details', kwargs={'identifier': shared_collection.id}), p)

            for edit_name in ['#name-edit']:
                expect(self.page.locator(edit_name)).to_contain_text("Edit")
                self.page.locator(edit_name).click()
                expect(self.page.locator(edit_name)).to_contain_text("Cancel")
                self.page.locator(edit_name).click()
                expect(self.page.locator(edit_name)).to_contain_text("Edit")

    def test_details_delete(self):
        shared_collection = SharedCollection.objects.create(name='some_shared_collection', collection=self.collection)

        with sync_playwright() as p:
            self.open(reverse('shared_collection_details', kwargs={'identifier': shared_collection.id}), p)

            self.page.locator("#delete_shared").click()
            self.page.get_by_text("Confirm").click()

            expect(self.page.locator("body")).to_contain_text("You have not shared any collections yet")

    def test_details_cancel_delete(self):
        shared_collection = SharedCollection.objects.create(name='some_shared_collection', collection=self.collection)

        with sync_playwright() as p:
            self.open(reverse('shared_collection_details', kwargs={'identifier': shared_collection.id}), p)

            expect(self.page.get_by_text("Confirm")).not_to_be_visible()
            expect(self.page.get_by_text("Cancel")).not_to_be_visible()
            expect(self.page.locator("#delete_shared")).to_be_visible()
            self.page.locator("#delete_shared").click()
            expect(self.page.get_by_text("Confirm")).to_be_visible()
            expect(self.page.get_by_text("Cancel")).to_be_visible()
            expect(self.page.locator("#delete_shared")).not_to_be_visible()
            self.page.get_by_text("Cancel").click()
            expect(self.page.get_by_text("Confirm")).not_to_be_visible()
            expect(self.page.get_by_text("Cancel")).not_to_be_visible()
            expect(self.page.locator("#delete_shared")).to_be_visible()
