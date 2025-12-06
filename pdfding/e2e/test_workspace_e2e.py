from django.contrib.auth.models import User
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from playwright.sync_api import sync_playwright


class TestWorkspaceE2ETestCase(PdfDingE2ETestCase):
    def test_create_workspace(self):
        with sync_playwright() as p:
            self.open(reverse('create_workspace'), p)
            self.page.get_by_role("textbox", name="Name:").click()
            self.page.get_by_role("textbox", name="Name:").fill("some_ws")
            self.page.get_by_role("button", name="Submit").click()

        changed_user = User.objects.get(id=self.user.id)
        created_ws = changed_user.profile.current_workspace

        self.assertNotEqual(self.user.id, changed_user.profile.current_workspace_id)
        self.assertEqual(created_ws.name, 'some_ws')
        self.assertEqual(created_ws.description, '')
        self.assertFalse(created_ws.personal_workspace)
