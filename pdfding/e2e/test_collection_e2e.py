from django.contrib.auth.models import User
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from playwright.sync_api import sync_playwright


class TestCollectionE2ETestCase(PdfDingE2ETestCase):
    def test_create_workspace(self):
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
