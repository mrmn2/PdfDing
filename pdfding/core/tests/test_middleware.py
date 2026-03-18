from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from users.models import Profile


class TestPdfDingLocaleMiddlewareUnauthenticated(TestCase):
    @override_settings(LANGUAGE_CODE='de')
    def test_unauthenticated(self):
        response = self.client.get(reverse('pdf_overview'))

        assert response.wsgi_request.LANGUAGE_CODE == 'de'


class TestPdfDingLocaleMiddlewareAuthenticated(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username=self.username, password=self.password, email='a@a.com')
        self.client.login(username=self.username, password=self.password)

    @override_settings(LANGUAGE_CODE='de')
    def test_auto(self):
        self.user.profile.language = Profile.LanguageChoice.AUTO
        self.user.profile.save()
        response = self.client.get(reverse('pdf_overview'))

        assert response.wsgi_request.LANGUAGE_CODE == 'de'

    @override_settings(LANGUAGE_CODE='de')
    def test_not_auto(self):
        self.user.profile.language = Profile.LanguageChoice.ENGLISH
        self.user.profile.save()
        response = self.client.get(reverse('pdf_overview'))

        assert response.wsgi_request.LANGUAGE_CODE == 'en'
