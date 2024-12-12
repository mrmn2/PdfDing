from allauth.socialaccount.models import SocialAccount
from django.test import override_settings
from django.urls import reverse
from helpers import PdfDingE2ENoLoginTestCase, PdfDingE2ETestCase
from playwright.sync_api import expect, sync_playwright


class UsersE2ETestCase(PdfDingE2ETestCase):
    def test_settings_change_theme(self):
        self.user.profile.dark_mode = 'Light'
        self.user.profile.theme_color = 'Green'
        self.user.profile.custom_theme_color = '#ffa385'
        self.user.profile.save()

        with sync_playwright() as p:
            self.open(reverse('profile-settings'), p)

            # test that light theme is used
            expect(self.page.locator('html')).to_have_attribute('class', 'light')
            expect(self.page.locator('html')).to_have_attribute('data-theme', 'Green')
            expect(self.page.locator("#theme")).to_contain_text("Light + Green")
            expect(self.page.locator('body')).to_have_css('background-color', 'rgba(0, 0, 0, 0)')
            expect(self.page.locator('header')).to_have_css('background-color', 'rgb(74, 222, 128)')

            # change to dark mode
            self.page.locator("#theme_edit").click()
            # check that selected option is correct
            expect(self.page.locator("#id_dark_mode")).to_have_value("Light")
            expect(self.page.locator("#id_theme_color")).to_have_value("Green")
            self.page.locator("#id_dark_mode").select_option("Dark")
            self.page.locator("#id_theme_color").select_option("Custom")
            self.page.get_by_role("button", name="Submit").click()

            # check that theme was changed to dark
            expect(self.page.locator('html')).to_have_attribute('class', 'dark')
            expect(self.page.locator('html')).to_have_attribute('data-theme', 'Custom')
            expect(self.page.locator("#theme")).to_contain_text("Dark + Custom")
            expect(self.page.locator('body')).to_have_css('background-color', 'rgb(30, 41, 59)')
            expect(self.page.locator('header')).to_have_css('background-color', 'rgb(255, 163, 133)')

            # trigger dropdown again
            self.page.locator("#theme_edit").click()
            # check that selected option is correct
            expect(self.page.locator("#id_dark_mode")).to_have_value("Dark")
            expect(self.page.locator("#id_theme_color")).to_have_value("Custom")

    def test_settings_email_change(self):
        with sync_playwright() as p:
            self.open(reverse('profile-settings'), p)

            # check email address before changing
            expect(self.page.locator('#email_address')).to_contain_text('a@a.com')
            expect(self.page.locator('content')).to_contain_text('Verified')

            # change email address
            self.page.locator('#email_edit').click()
            self.page.locator('#id_email').click()
            self.page.locator('#id_email').press('ControlOrMeta+a')
            self.page.locator('#id_email').fill('a@b.com')
            self.page.get_by_role('button', name='Submit').click()

            # check email address after changing
            expect(self.page.locator('#email_address')).to_contain_text('a@b.com')
            expect(self.page.locator('content')).to_contain_text('Not verified')

    def test_settings_change_custom_color(self):
        with sync_playwright() as p:
            self.open(reverse('profile-settings'), p)

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
            self.open(reverse('profile-settings'), p)

            # check inverted color mode before changing
            expect(self.page.locator("#pdf_inverted_mode")).to_contain_text("Inverted PDF colors are disabled")

            # change inverted color mode
            self.page.locator("#pdf_inverted_mode_edit").click()
            self.page.locator("#id_pdf_inverted_mode").select_option("Enabled")
            self.page.get_by_role("button", name="Submit").click()

            # check inverted color mode after changing
            expect(self.page.locator("#pdf_inverted_mode")).to_contain_text("Inverted PDF colors are enabled")

    def test_settings_change_show_progress_bar(self):
        with sync_playwright() as p:
            self.open(reverse('profile-settings'), p)

            # check inverted color mode before changing
            expect(self.page.locator("#show_progress_bars")).to_contain_text("Read progress bars are enabled")

            # change inverted color mode
            self.page.locator("#show_progress_bars_edit").click()
            self.page.locator("#id_show_progress_bars").select_option("Disabled")
            self.page.get_by_role("button", name="Submit").click()

            # check inverted color mode after changing
            expect(self.page.locator("#show_progress_bars")).to_contain_text("Read progress bars are disabled")

    def test_settings_change_pdf_per_page(self):
        with sync_playwright() as p:
            self.open(reverse('profile-settings'), p)

            # check pdfs per page before changing
            expect(self.page.locator("#pdfs_per_page")).to_contain_text("25")

            # change pdfs per page
            self.page.locator("#pdfs_per_page_edit").click()
            self.page.locator("#id_pdfs_per_page").select_option("50")
            self.page.get_by_role("button", name="Submit").click()

            # check pdfs per page after changing
            expect(self.page.locator("#pdfs_per_page")).to_contain_text("50")

    def test_settings_delete(self):
        with sync_playwright() as p:
            self.open(reverse('profile-settings'), p)

            # we just check if delete button is displayed, rest is covered by unit test
            self.page.get_by_role('link', name='Delete').click()
            expect(self.page.get_by_role('button')).to_contain_text('Yes, I want to delete my account')

    def test_settings_edit_cancel(self):
        with sync_playwright() as p:
            self.open(reverse('profile-settings'), p)

            for name in [
                '#email_edit',
                '#theme_edit',
                '#custom_theme_color_edit',
                '#pdf_inverted_mode_edit',
                '#pdfs_per_page_edit',
                '#show_progress_bars_edit',
            ]:
                self.page.locator(name).click()
                expect(self.page.locator(name)).to_contain_text('Cancel')
                self.page.get_by_role('link', name='Cancel').click()
                expect(self.page.locator(name)).to_contain_text('Edit')

    def test_settings_change_password(self):
        with sync_playwright() as p:
            self.open(reverse('profile-settings'), p)

            # we just check if allauth change password is displayed
            self.page.get_by_role('link', name='Edit').click()
            expect(self.page.get_by_role('button')).to_contain_text('Change Password')

    def test_settings_social_only(self):
        # test that email and password settings are not present for oidc users
        social_account = SocialAccount.objects.create(user=self.user)
        self.user.socialaccount_set.set([social_account])

        with sync_playwright() as p:
            self.open(reverse('profile-settings'), p)

            expect(self.page.locator('#email_edit')).to_have_count(0)
            expect(self.page.get_by_text("Password")).to_have_count(0)

    def test_header_dropdown(self):
        with sync_playwright() as p:
            self.open(reverse('pdf_overview'), p)
            self.page.get_by_role("banner").get_by_role("list").locator("li").filter(
                has_text="Logged in as a@a.com User ID:"
            ).locator("a").first.click()
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

    def test_login_header_normal(self):
        with sync_playwright() as p:
            self.open(reverse('home'), p)
            # login and signup should be displayed if not in oidc only mode
            expect(self.page.get_by_role('banner')).to_contain_text('Login Signup')

    @override_settings(SOCIALACCOUNT_ONLY=True)
    def test_login_header_oidc_only(self):
        with sync_playwright() as p:
            self.open(reverse('home'), p)
            expect(self.page.get_by_role('banner')).to_contain_text('Login')
            # signup should not be displayed in oidc only mode
            expect(self.page.get_by_role('banner')).not_to_contain_text('Signup')

    @override_settings(SIGNUP_CLOSED=True)
    def test_login_header_signup_disabled(self):
        with sync_playwright() as p:
            self.open(reverse('home'), p)
            expect(self.page.get_by_role('banner')).to_contain_text('Login')
            # signup should not be displayed in signup_disabled mode
            expect(self.page.get_by_role('banner')).not_to_contain_text('Signup')

    @override_settings(DEFAULT_THEME='dark', DEFAULT_THEME_COLOR='Blue')
    def test_default_theme(self):
        with sync_playwright() as p:
            self.open(reverse('home'), p)

            # test that light theme is used
            expect(self.page.locator('html')).to_have_attribute('class', 'dark')
            expect(self.page.locator('html')).to_have_attribute('data-theme', 'Blue')
            expect(self.page.locator('body')).to_have_css('background-color', 'rgb(30, 41, 59)')
            expect(self.page.locator('header')).to_have_css('background-color', 'rgb(71, 147, 204)')
