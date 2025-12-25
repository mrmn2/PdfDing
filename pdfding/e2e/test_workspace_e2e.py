from django.contrib.auth.models import User
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models.workspace_models import Workspace
from pdf.services.workspace_services import create_workspace
from playwright.sync_api import expect, sync_playwright


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

    def test_details(self):
        ws = self.user.profile.current_workspace

        with sync_playwright() as p:
            self.open(reverse('workspace_details', kwargs={'identifier': ws.id}), p)

            expect(self.page.locator("#name")).to_contain_text("Personal")
            expect(self.page.locator("#personal_workspace")).to_contain_text("Yes")
            expect(self.page.locator("#description")).to_contain_text("Personal Workspace")

    def test_change_details(self):
        ws = self.user.profile.current_workspace

        # also test changing from inactive to active
        with sync_playwright() as p:
            self.open(reverse('workspace_details', kwargs={'identifier': ws.id}), p)

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

    def test_cancel_delete(self):
        other_ws = create_workspace('other_ws', self.user)

        with sync_playwright() as p:
            # only display one pdf
            self.open(reverse('workspace_details', kwargs={'identifier': other_ws.id}), p)

            expect(self.page.locator("#delete_workspace_modal").first).not_to_be_visible()
            self.page.locator("#delete-workspace").click()
            expect(self.page.locator("#delete_workspace_modal").first).to_be_visible()
            self.page.locator("#cancel_delete").get_by_text("Cancel").click()
            expect(self.page.locator("#delete_workspace_modal").first).not_to_be_visible()

    def test_delete(self):
        other_ws = create_workspace('other_ws', self.user)
        self.user.profile.current_workspace_id = other_ws.id
        self.user.profile.save()

        with sync_playwright() as p:
            self.open(reverse('workspace_details', kwargs={'identifier': other_ws.id}), p)

            self.page.locator("#delete-workspace").click()
            self.page.locator("#confirm_delete").get_by_text("Submit").click()
            expect(self.page.locator("#delete_workspace_modal").first).not_to_be_visible()

        assert not Workspace.objects.filter(id=other_ws.id).count()

    def test_delete_not_visible_personal(self):
        with sync_playwright() as p:
            self.open(reverse('workspace_details', kwargs={'identifier': self.user.id}), p)

            expect(self.page.locator("#delete-workspace").first).not_to_be_visible()
