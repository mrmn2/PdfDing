from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.services.workspace_services import create_collection
from playwright.sync_api import expect, sync_playwright


class TestCollectionE2ETestCase(PdfDingE2ETestCase):
    def test_create_collection(self):
        with sync_playwright() as p:
            self.open(reverse('create_collection'), p)
            self.page.get_by_role("textbox", name="Name:").click()
            self.page.get_by_role("textbox", name="Name:").fill("some_collection")
            self.page.get_by_role("button", name="Submit").click()

        changed_user = User.objects.get(id=self.user.id)
        created_collection = changed_user.profile.current_workspace.collections[1]

        self.assertEqual(created_collection.name, 'some_collection')
        self.assertEqual(created_collection.description, '')
        self.assertFalse(created_collection.default_collection)

    def test_change_collection(self):
        ws = self.user.profile.current_workspace
        create_collection(ws, 'other_collection')
        # make sure collection shown is not all
        self.user.profile.current_collection_id = self.user.profile.current_workspace_id
        self.user.profile.save()

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("#current_collection_name")).to_contain_text("Default")
            self.page.locator("#current_collection_name").click()
            self.page.locator("#collection_modal").get_by_text("other_collection").click()
            expect(self.page.locator("#current_collection_name")).to_contain_text("other_collection")

    def test_details(self):
        collection = self.user.profile.current_collection

        with sync_playwright() as p:
            self.open(reverse('collection_details', kwargs={'identifier': collection.id}), p)

            expect(self.page.locator("#name")).to_contain_text("Defaul")
            expect(self.page.locator("#default_collection")).to_contain_text("Yes")
            expect(self.page.locator("#description")).to_contain_text("Default Collection")

    @patch('pdf.services.collection_services.move')
    def test_change_details(self, mock_move):
        collection = self.user.profile.current_collection

        with sync_playwright() as p:
            self.open(reverse('collection_details', kwargs={'identifier': collection.id}), p)

            self.page.locator("#name-edit").click()
            self.page.locator("#id_name").dblclick()
            self.page.locator("#id_name").fill("other-name")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#name")).to_contain_text("other-name")
            self.page.locator("#description-edit").click()
            self.page.locator("#id_description").click()
            self.page.locator("#id_description").fill("other description")
            self.page.get_by_role("button", name="Submit").click()
            expect(self.page.locator("#description")).to_contain_text("other description")

    def test_details_change_collection(self):
        create_collection(self.user.profile.current_workspace, 'other_collection')

        collection = self.user.profile.current_collection

        with sync_playwright() as p:
            self.open(reverse('collection_details', kwargs={'identifier': collection.id}), p)
            expect(self.page.locator("#current_collection_name")).to_contain_text("Default")
            self.page.locator("#current_collection_name").click()
            self.page.get_by_text("other_collection").click()
            expect(self.page.locator("#current_collection_name")).to_contain_text("other_collection")
