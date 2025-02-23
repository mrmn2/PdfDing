from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client
from playwright.sync_api import BrowserContext, Page, Playwright, expect


class PdfDingE2ETestCase(StaticLiveServerTestCase):
    username = 'user'
    password = '12345'
    email = 'a@a.com'

    def setUp(self, login: bool = True) -> None:
        super(StaticLiveServerTestCase, self).setUp()
        self.client = Client()
        self.user = User.objects.create_user(username=self.username, password=self.password, email=self.email)

        # set email address to verified
        self.user.save()  # this will create email address object if not yet existing
        email_address = EmailAddress.objects.get_primary(self.user)
        email_address.verified = True
        email_address.save()

        self.user.profile.tags_open = True
        self.user.profile.save()

        if login:
            self.client.login(username=self.username, password=self.password)
            self.cookie = self.client.cookies['sessionid']

        self.login = login

    def setup_browser(self, playwright) -> BrowserContext:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()

        # create dummy cookie tests without a logged in user
        if self.login:
            cookie_value = self.cookie.value
        else:
            cookie_value = 'bla'

        context.add_cookies(
            [
                {
                    'name': 'sessionid',
                    'value': cookie_value,
                    'domain': self.live_server_url.replace('http:', ''),
                    'path': '/',
                }
            ]
        )

        return context

    def open(self, url: str, playwright: Playwright) -> Page:
        browser = self.setup_browser(playwright)
        self.page = browser.new_page()
        self.page.goto(self.live_server_url + url)
        self.num_loads = 0

        return self.page


class PdfDingE2ENoLoginTestCase(PdfDingE2ETestCase):
    def setUp(self, login=False):
        super().setUp(login=login)


def cancel_delete_helper(page):
    expect(page.get_by_text("Confirm")).not_to_be_visible()
    expect(page.get_by_role("button", name="Cancel")).not_to_be_visible()
    expect(page.get_by_role("button", name="Delete")).to_be_visible()
    page.get_by_role("button", name="Delete").click()
    expect(page.get_by_text("Confirm")).to_be_visible()
    expect(page.get_by_role("button", name="Cancel")).to_be_visible()
    expect(page.get_by_role("button", name="Delete")).not_to_be_visible()
    page.get_by_role("button", name="Cancel").click()
    expect(page.get_by_text("Confirm")).not_to_be_visible()
    expect(page.get_by_role("button", name="Cancel")).not_to_be_visible()
    expect(page.get_by_role("button", name="Delete")).to_be_visible()
