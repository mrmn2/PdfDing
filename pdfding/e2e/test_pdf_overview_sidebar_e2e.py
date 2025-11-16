from django.contrib.auth.models import User
from django.urls import reverse
from helpers import PdfDingE2ETestCase
from pdf.models.pdf_models import Pdf, Tag
from playwright.sync_api import expect, sync_playwright


class TagE2ETestCase(PdfDingE2ETestCase):
    def setUp(self, login: bool = True) -> None:
        super().setUp()

        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')
        self.tag = Tag.objects.create(name='bla', owner=self.user.profile)
        pdf.tags.set([self.tag])

    def test_sidebar_tags_normal_mode(self):
        profile = self.user.profile
        profile.tag_tree_mode = False
        profile.save()

        tags = []
        tag_names = ['hobbies/sports', 'programming/python/django', 'other']

        for tag_name in tag_names:
            tag = Tag.objects.create(name=tag_name, owner=self.user.profile)
            tags.append(tag)

        pdf = Pdf.objects.create(owner=self.user.profile, name='some_pdf')
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

    def test_sidebar_tag_tree_mode(self):
        profile = self.user.profile
        profile.tag_tree_mode = True
        profile.save()

        tags = []
        # we use 1_programming as previously tags starting with a number did not work
        tag_names = ['1_programming/python/django', 'other']

        for tag_name in tag_names:
            tag = Tag.objects.create(name=tag_name, owner=self.user.profile)
            tags.append(tag)

        pdf = Pdf.objects.create(owner=self.user.profile, name='some_pdf')
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
        profile.tag_tree_mode = False
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
        profile.tag_tree_mode = True
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
        profile.tag_tree_mode = False
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
        profile.tag_tree_mode = True
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

    def test_open_tag_mode_settings(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.locator("#tag_mode_settings")).not_to_be_visible()

            self.page.locator("#show_tag_mode_settings").click()
            expect(self.page.locator("#tag_mode_settings")).to_be_visible()
            self.page.get_by_role("banner").click()
            expect(self.page.locator("#tag_mode_settings")).not_to_be_visible()

    def test_change_tag_mode(self):
        profile = self.user.profile
        profile.tag_tree_mode = False
        profile.save()

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            self.page.locator("#show_tag_mode_settings").click()
            self.page.locator("#tag_mode_toggle").click()

        changed_user = User.objects.get(id=self.user.id)
        self.assertTrue(changed_user.profile.tag_tree_mode)

    def test_open_collapse_tags(self):
        profile = self.user.profile
        profile.tags_open = False
        profile.save()

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)

            expect(self.page.locator("#tag-bla")).not_to_be_visible()
            self.page.locator("#tags_open_collapse_toggle").click()
            expect(self.page.locator("#tag-bla")).to_be_visible()

        changed_user = User.objects.get(id=self.user.id)
        self.assertTrue(changed_user.profile.tags_open)
