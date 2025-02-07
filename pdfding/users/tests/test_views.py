from unittest.mock import Mock, patch

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from pdf.models import Pdf, Tag
from users import forms
from users.models import Profile


class TestAuthRelated(TestCase):
    def test_login_required(self):
        response = self.client.get(reverse('pdf_overview'))

        self.assertRedirects(response, f'/accountlogin/?next={reverse('pdf_overview')}', status_code=302)

    def test_login(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)

    def test_signup(self):
        response = self.client.get(reverse('signup'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/signup.html')

    @override_settings(SIGNUP_CLOSED=True)
    def test_signup_closed(self):
        response = self.client.get(reverse('signup'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/signup_closed.html')

    def test_password_reset(self):
        response = self.client.get(reverse('password_reset'))

        self.assertEqual(response.status_code, 200)

    def test_password_reset_done(self):
        response = self.client.get(reverse('password_reset_done'))

        self.assertEqual(response.status_code, 200)

    def test_oidc_login(self):
        response = self.client.get(reverse('oidc_login'))

        self.assertEqual(response.status_code, 200)

    def test_oidc_callback(self):
        response = self.client.get(reverse('oidc_callback'))

        self.assertEqual(response.status_code, 200)


class TestProfileViews(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username=self.username, password=self.password, email='a@a.com')
        self.client.login(username=self.username, password=self.password)

    def test_settings(self):
        # test without social account
        response = self.client.get(reverse('profile-settings'))
        self.assertEqual(response.context['uses_social'], False)

        # test with social account
        social_account = SocialAccount.objects.create(user=self.user)
        self.user.socialaccount_set.set([social_account])

        response = self.client.get(reverse('profile-settings'))
        self.assertEqual(response.context['uses_social'], True)

    def test_change_settings_get_no_htmx(self):
        response = self.client.get(reverse('profile-setting-change', kwargs={'field_name': 'email'}))

        # target_status_code=302 because the '/' will redirect to the pdf overview
        self.assertRedirects(response, '/', status_code=302, target_status_code=302)

    def test_change_settings_get_htmx(self):
        self.user.profile.dark_mode = 'Light'
        self.user.profile.theme_color = 'Green'
        self.user.profile.save()

        headers = {'HTTP_HX-Request': 'true'}

        field_names = [
            'pdf_inverted_mode',
            'custom_theme_color',
            'pdfs_per_page',
            'theme',
            'email',
            'show_progress_bars',
            'show_thumbnails',
            'tags_tree_mode',
        ]
        form_list = [
            forms.GenericUserFieldForm,
            forms.CustomThemeColorForm,
            forms.GenericUserFieldForm,
            forms.GenericUserFieldForm,
            forms.EmailForm,
            forms.GenericUserFieldForm,
            forms.GenericUserFieldForm,
            forms.GenericUserFieldForm,
        ]
        initial_dicts = [
            {'pdf_inverted_mode': 'Disabled'},
            {'custom_theme_color': '#ffa385'},
            {'pdfs_per_page': 25},
            {'dark_mode': 'Light', 'theme_color': 'Green'},
            {'email': 'a@a.com'},
            {'show_progress_bars': 'Enabled'},
            {'show_thumbnails': 'Disabled'},
            {'tags_tree_mode': 'Enabled'},
        ]

        for field_name, form, initial_dict in zip(field_names, form_list, initial_dicts):
            response = self.client.get(reverse('profile-setting-change', kwargs={'field_name': field_name}), **headers)

            self.assertIsInstance(response.context['form'], form)
            self.assertEqual(initial_dict, response.context['form'].initial)

    def test_change_settings_post_invalid_form(self):
        # follow=True is needed for getting the message
        response = self.client.post(
            reverse('profile-setting-change', kwargs={'field_name': 'custom_theme_color'}),
            data={"custom_theme_color": 'invalid'},
            follow=True,
        )
        message = list(response.context['messages'])[0]

        self.assertEqual(message.message, 'Only valid hex colors are allowed! E.g.: #ffa385.')
        self.assertEqual(message.tags, 'warning')

    def test_change_settings_email_post_email_exists(self):
        User.objects.create_user(username='other_user', password=self.password, email='a@b.com')
        # follow=True is needed for getting the message
        response = self.client.post(
            reverse('profile-setting-change', kwargs={'field_name': 'email'}), data={"email": 'a@b.com'}, follow=True
        )
        message = list(response.context['messages'])[0]

        self.assertEqual(message.message, 'a@b.com is already in use.')
        self.assertEqual(message.tags, 'warning')

    @patch('users.views.send_email_confirmation')
    def test_change_settings_email_post_correct(self, mock_send):
        self.client.post(reverse('profile-setting-change', kwargs={'field_name': 'email'}), data={'email': 'a@c.com'})

        # get the user and check if email was changed
        user = User.objects.get(username=self.username)
        mock_send.assert_called()
        self.assertEqual(user.email, 'a@c.com')

    def test_change_settings_custom_theme_color(self):
        self.client.post(
            reverse('profile-setting-change', kwargs={'field_name': 'custom_theme_color'}),
            data={'custom_theme_color': '#b5edff'},
        )

        # get the user and check if email was changed
        user = User.objects.get(username=self.username)
        self.assertEqual(user.profile.custom_theme_color, '#b5edff')
        self.assertEqual(user.profile.custom_theme_color_secondary, '#91becc')
        self.assertEqual(user.profile.custom_theme_color_tertiary_1, '#6d8e99')
        self.assertEqual(user.profile.custom_theme_color_tertiary_2, '#d3f4ff')

    def test_change_settings_dark_mode_post_correct(self):
        self.user.profile.dark_mode = 'Light'
        self.user.profile.theme_color = 'Green'
        self.user.profile.save()

        self.assertEqual(self.user.profile.dark_mode, 'Light')
        self.assertEqual(self.user.profile.theme_color, 'Green')
        self.client.post(
            reverse('profile-setting-change', kwargs={'field_name': 'theme'}),
            data={'dark_mode': 'Dark', 'theme_color': 'Blue'},
        )

        # get the user and check if dark mode was changed
        user = User.objects.get(username=self.username)
        self.assertEqual(user.profile.dark_mode, 'Dark')
        self.assertEqual(user.profile.theme_color, 'Blue')

    def test_change_settings_normal_post_correct(self):
        for field_name, val_before, val_after in zip(
            [
                'pdfs_per_page',
                'pdf_inverted_mode',
                'tags_tree_mode',
                'show_progress_bars',
                'show_thumbnails',
            ],
            [25, 'Disabled', 'Enabled', 'Enabled', 'Disabled'],
            [10, 'Enabled', 'Disabled', 'Disabled', 'Enabled'],
        ):
            self.assertEqual(getattr(self.user.profile, field_name), val_before)
            self.client.post(
                reverse('profile-setting-change', kwargs={'field_name': field_name}), data={field_name: val_after}
            )

            user = User.objects.get(username=self.username)
            self.assertEqual(getattr(user.profile, field_name), val_after)

    def test_delete_post(self):
        # in this test we test that the user is successfully deleted
        # we also test that the associated profile, pdfs, and tags are also deleted
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_1')
        tags = [Tag.objects.create(name='tag', owner=pdf.owner)]
        pdf.tags.set(tags)

        for model_class in [Profile, Pdf, Tag]:
            # assert there is a profile, pdf and tag
            self.assertEqual(model_class.objects.all().count(), 1)

        # follow=True is needed for getting the message
        response = self.client.post(reverse('profile-delete'), follow=True)
        message = list(response.context['messages'])[0]

        self.assertFalse(User.objects.filter(username=self.username).exists())
        self.assertEqual(message.message, 'Your Account was successfully deleted.')
        self.assertEqual(message.tags, 'success')
        for model_class in [Profile, Pdf, Tag]:
            # assert there is no profile, pdf and tag
            self.assertEqual(model_class.objects.all().count(), 0)


class TestDemoViews(TestCase):
    def test_create_demo_user_post_no_htmx(self):
        response = self.client.post(reverse('create_demo_user'))

        # target_status_code=302 because the '/' will redirect to the pdf overview
        self.assertRedirects(response, reverse('pdf_overview'), status_code=302, target_status_code=302)

    @override_settings(DEMO_MODE=False)
    def test_create_demo_user_post_normal_mode(self):
        # in normal mode user creation is not allowed.
        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.post(reverse('create_demo_user'), **headers)

        # target_status_code=302 because the '/' will redirect to the pdf overview
        self.assertRedirects(response, reverse('pdf_overview'), status_code=302, target_status_code=302)

    @patch('users.views.create_demo_user')
    @patch('users.views.uuid4', return_value='123456789')
    @override_settings(DEMO_MODE=True)
    def test_create_demo_user_post_demo_mode(self, mock_uuid4, mock_create_demo_user):
        email = '12345678@pdfding.com'
        mock_user = Mock()
        mock_user.email = email
        mock_create_demo_user.return_value = mock_user

        self.assertEqual(User.objects.all().count(), 0)

        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.post(reverse('create_demo_user'), **headers)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partials/demo_user.html')
        mock_create_demo_user.assert_called_once_with(email, 'demo')
        self.assertEqual(response.context['email'], email)
        self.assertEqual(response.context['password'], 'demo')

    @patch('users.views.User.objects.get')
    @patch('users.views.create_demo_user', side_effect=IntegrityError)
    @patch('users.views.uuid4', return_value='123456789')
    @override_settings(DEMO_MODE=True)
    def test_create_demo_user_post_demo_mode_exception(self, mock_uuid4, mock_create_demo_user, mock_get):
        email = '12345678@pdfding.com'
        mock_user = Mock()
        mock_user.email = email
        mock_get.return_value = mock_user

        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.post(reverse('create_demo_user'), **headers)
        mock_create_demo_user.assert_called_once_with(email, 'demo')
        mock_get.assert_called_once_with(email=email)
        self.assertTemplateUsed(response, 'partials/demo_user.html')
        self.assertEqual(response.context['email'], email)
        self.assertEqual(response.context['password'], 'demo')

    @patch('users.views.randint')
    @patch('users.views.User.objects.get')
    @patch('users.views.create_demo_user')
    @patch('users.views.uuid4', return_value='123456789')
    @override_settings(DEMO_MAX_USERS=5)
    @override_settings(DEMO_MODE=True)
    def test_create_demo_user_post_demo_mode_too_many_users(
        self, mock_uuid4, mock_create_demo_user, mock_get, mock_randint
    ):
        for i in range(5):
            User.objects.create_user(username=f'user_{i}', password='password')

        email = '12345678@pdfding.com'
        mock_user = Mock()
        mock_user.email = email
        mock_get.return_value = mock_user
        mock_randint.return_value = 3

        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.post(reverse('create_demo_user'), **headers)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partials/demo_user.html')
        mock_randint.assert_called_once_with(1, 5)
        mock_get.assert_called_once_with(id=3)

        self.assertEqual(response.context['email'], email)
        self.assertEqual(response.context['password'], 'demo')
