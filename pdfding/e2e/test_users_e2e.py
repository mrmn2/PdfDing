from unittest.mock import Mock, patch

from allauth.socialaccount.models import SocialAccount
from django.test import override_settings
from django.urls import reverse
from helpers import PdfDingE2ENoLoginTestCase, PdfDingE2ETestCase
from playwright.sync_api import expect, sync_playwright


class UsersE2ETestCase(PdfDingE2ETestCase):
    def test_settings_change_theme(self):
        self.user.profile.dark_mode = 'Light'
        self.user.profile.save()

        with sync_playwright() as p:
            self.open(reverse('ui_settings'), p)

            # test that light theme is used
            expect(self.page.locator('html')).to_have_attribute('class', 'light')
            expect(self.page.locator("#theme")).to_contain_text("Light")
            expect(self.page.locator('body')).to_have_css('background-color', 'oklch(0.984 0.003 247.858)')

            # change to dark mode
            self.page.locator("#theme_edit").click()
            # check that selected option is correct
            expect(self.page.locator("#id_dark_mode")).to_have_value("Light")
            self.page.locator("#id_dark_mode").select_option("Dark")
            self.page.get_by_role("button", name="Submit").click()

            # check that theme was changed to dark
            expect(self.page.locator('html')).to_have_attribute('class', 'dark')
            expect(self.page.locator("#theme")).to_contain_text("Dark")
            expect(self.page.locator('body')).to_have_css('background-color', 'oklch(0.208 0.042 265.755)')

            # trigger dropdown again
            self.page.locator("#theme_edit").click()
            # check that selected option is correct
            expect(self.page.locator("#id_dark_mode")).to_have_value("Dark")

            # change to creme mode
            self.page.locator("#id_dark_mode").select_option("Creme")
            self.page.get_by_role("button", name="Submit").click()

            # check that theme was changed to creme
            expect(self.page.locator('html')).to_have_attribute('class', 'creme')
            expect(self.page.locator("#theme")).to_contain_text("Creme")
            expect(self.page.locator('body')).to_have_css('background-color', 'rgb(226, 220, 208)')

    def test_settings_change_theme_color(self):
        self.user.profile.theme_color = 'Green'
        self.user.profile.custom_theme_color = '#ffa385'
        self.user.profile.save()

        with sync_playwright() as p:
            self.open(reverse('ui_settings'), p)

            # test that light theme is used
            expect(self.page.locator('html')).to_have_attribute('data-theme', 'Green')
            expect(self.page.locator("#theme_color")).to_contain_text("Green")
            expect(self.page.locator('#logo_div')).to_have_css('background-color', 'rgb(74, 222, 128)')

            # change to dark mode
            self.page.locator("#theme_color_edit").click()
            # check that selected option is correct
            expect(self.page.locator("#id_theme_color")).to_have_value("Green")
            self.page.locator("#id_theme_color").select_option("Custom")
            self.page.get_by_role("button", name="Submit").click()

            # check that theme was changed to dark
            expect(self.page.locator('html')).to_have_attribute('data-theme', 'Custom')
            expect(self.page.locator("#theme_color")).to_contain_text("Custom")
            expect(self.page.locator('#logo_div')).to_have_css('background-color', 'rgb(255, 163, 133)')

            # trigger dropdown again
            self.page.locator("#theme_color_edit").click()
            # check that selected option is correct
            expect(self.page.locator("#id_theme_color")).to_have_value("Custom")

    def test_settings_email_change(self):
        with sync_playwright() as p:
            self.open(reverse('account_settings'), p)

            # check email address before changing
            expect(self.page.locator('#email_address')).to_contain_text('a@a.com')
            expect(self.page.locator('body')).to_contain_text('Verified')

            # change email address
            self.page.locator('#email_edit').click()
            self.page.locator('#id_email').click()
            self.page.locator('#id_email').press('ControlOrMeta+a')
            self.page.locator('#id_email').fill('a@b.com')
            self.page.get_by_role('button', name='Submit').click()

            # check email address after changing
            expect(self.page.locator('#email_address')).to_contain_text('a@b.com')
            expect(self.page.locator('body')).to_contain_text('Not verified')

    def test_settings_change_custom_color(self):
        with sync_playwright() as p:
            self.open(reverse('ui_settings'), p)

            # check custom color before changing
            expect(self.page.locator("#custom_theme_color")).to_contain_text("#ffa385")

            # change custom color
            self.page.locator("#custom_theme_color_edit").click()
            self.page.locator("#id_custom_theme_color").fill("#95c2d6")
            self.page.get_by_role("button", name="Submit").click()

            # check custom color after changing
            expect(self.page.locator("#custom_theme_color")).to_contain_text("95c2d6")

    def test_settings_change_inverted_pdf(self):
        with sync_playwright() as p:
            self.open(reverse('ui_settings'), p)

            # check inverted color mode before changing
            expect(self.page.locator("#pdf_inverted_mode")).to_contain_text("Disabled")

            # change inverted color mode
            self.page.locator("#pdf_inverted_mode_edit").click()
            self.page.locator("#id_pdf_inverted_mode").select_option("Enabled")
            self.page.get_by_role("button", name="Submit").click()

            # check inverted color mode after changing
            expect(self.page.locator("#pdf_inverted_mode")).to_contain_text("Enabled")

    def test_settings_change_show_progress_bars(self):
        with sync_playwright() as p:
            self.open(reverse('ui_settings'), p)

            # check inverted color mode before changing
            expect(self.page.locator("#show_progress_bars")).to_contain_text("Enabled")

            # change inverted color mode
            self.page.locator("#show_progress_bars_edit").click()
            self.page.locator("#id_show_progress_bars").select_option("Disabled")
            self.page.get_by_role("button", name="Submit").click()

            # check inverted color mode after changing
            expect(self.page.locator("#show_progress_bars")).to_contain_text("Disabled")

    def test_settings_delete(self):
        with sync_playwright() as p:
            self.open(reverse('danger_settings'), p)

            # we just check if delete button is displayed, rest is covered by unit test
            self.page.get_by_role('link', name='Delete').click()
            expect(self.page.get_by_role('button')).to_contain_text('Yes, I want to delete my account')

    def test_settings_edit_cancel_account_settings(self):
        with sync_playwright() as p:
            self.open(reverse('account_settings'), p)

            for name in ['#email_edit']:
                self.page.locator(name).click()
                expect(self.page.locator(name)).to_contain_text('Cancel')
                self.page.get_by_text("Cancel").click()
                expect(self.page.locator(name)).to_contain_text('Edit')

    def test_settings_edit_cancel_ui_settings(self):
        with sync_playwright() as p:
            self.open(reverse('ui_settings'), p)

            for name in ['#theme_edit', '#theme_color_edit', '#custom_theme_color_edit', '#pdf_inverted_mode_edit']:
                self.page.locator(name).click()
                expect(self.page.locator(name)).to_contain_text('Cancel')
                self.page.get_by_text("Cancel").click()
                expect(self.page.locator(name)).to_contain_text('Edit')

    def test_settings_change_password(self):
        with sync_playwright() as p:
            self.open(reverse('account_settings'), p)

            # we just check if allauth change password is displayed
            self.page.get_by_role('link', name='Edit').click()
            expect(self.page.get_by_role('button')).to_contain_text('Change Password')

    def test_settings_social_only(self):
        # test that email and password settings are not present for oidc users
        social_account = SocialAccount.objects.create(user=self.user)
        self.user.socialaccount_set.set([social_account])

        with sync_playwright() as p:
            self.open(reverse('account_settings'), p)

            expect(self.page.locator('#email_edit')).to_have_count(0)
            expect(self.page.get_by_text("Password")).to_have_count(0)

    def test_header_dropdown(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            self.page.locator("#open-user-dropdown > div:nth-child(3)").click()
            expect(self.page.get_by_role("banner")).to_contain_text("a@a.com")
            expect(self.page.get_by_role("banner")).to_contain_text(f"User ID: {self.user.id}")

    def test_header_non_admin(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.get_by_role("banner")).not_to_contain_text("Admin")

    def test_header_admin(self):
        self.user.is_staff = True
        self.user.is_superuser = True

        self.user.save()

        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            expect(self.page.get_by_role("banner")).to_contain_text("Admin")


class UsersLoginE2ETestCase(PdfDingE2ENoLoginTestCase):
    def test_login(self):
        with sync_playwright() as p:
            self.open(reverse('home'), p)
            expect(self.page.get_by_role('heading')).to_contain_text('Sign In')
            self.page.get_by_placeholder('Email address').click()
            self.page.get_by_placeholder('Email address').fill(self.email)
            self.page.get_by_placeholder('Email address').press('Tab')
            self.page.get_by_placeholder('Password').fill(self.password)
            self.page.get_by_role('button', name='Sign In', exact=True).click()
            expect(self.page.locator('body')).to_contain_text('PDFs')

            # demo mode info should not be visible
            expect(self.page.locator("#demo_mode")).not_to_be_visible()

    def test_login_header_normal(self):
        with sync_playwright() as p:
            self.open(reverse('home'), p)
            # login and signup should be displayed if not in oidc only mode
            expect(self.page.get_by_role('banner')).to_contain_text('Sign in Sign up')

    @override_settings(SOCIALACCOUNT_ONLY=True)
    def test_login_header_oidc_only(self):
        with sync_playwright() as p:
            self.open(reverse('home'), p)
            expect(self.page.get_by_role('banner')).to_contain_text('Sign in')
            # signup should not be displayed in oidc only mode
            expect(self.page.get_by_role('banner')).not_to_contain_text('Sign up')

    @override_settings(SIGNUP_CLOSED=True)
    def test_login_header_signup_disabled(self):
        with sync_playwright() as p:
            self.open(reverse('home'), p)
            expect(self.page.get_by_role('banner')).to_contain_text('Sign in')
            # signup should not be displayed in signup_disabled mode
            expect(self.page.get_by_role('banner')).not_to_contain_text('Sign up')

    @override_settings(DEFAULT_THEME='dark', DEFAULT_THEME_COLOR='Blue')
    def test_default_theme(self):
        with sync_playwright() as p:
            self.open(reverse('home'), p)

            # test that light theme is used
            expect(self.page.locator('html')).to_have_attribute('class', 'dark')
            expect(self.page.locator('html')).to_have_attribute('data-theme', 'Blue')
            expect(self.page.locator('body')).to_have_css('background-color', 'oklch(0.208 0.042 265.755)')
            expect(self.page.locator('#logo_div')).to_have_css('background-color', 'rgb(71, 147, 204)')

    @patch('users.views.create_demo_user')
    @patch('users.views.uuid4', return_value='123456789')
    @override_settings(DEMO_MODE=True)
    def test_login_demo_mode(self, mock_uuid4, mock_create_demo_user):
        email = '12345678@pdfding.com'
        mock_user = Mock()
        mock_user.email = email
        mock_create_demo_user.return_value = mock_user

        with sync_playwright() as p:
            self.open(reverse('home'), p)
            expect(self.page.locator("#demo_mode")).to_be_visible()

            self.page.get_by_role("button", name="Create User").click()
            expect(self.page.locator("#demo_user")).to_contain_text("Demo user successfully created")
            expect(self.page.locator("#demo_user")).to_contain_text(
                f"You can log into your temporary account with: {email} / demo"
            )
