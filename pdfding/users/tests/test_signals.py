from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from users.models import Profile
from users.signals import oidc_handle_admin_rights


class TestSignals(TestCase):
    @override_settings(DEFAULT_THEME='dark', DEFAULT_THEME_COLOR='Gray')
    def test_user_postsave(self):
        input_mail = 'a@a.com'

        user = User.objects.create_user(username='user', password='12345', email=input_mail)

        # check that the profile exists
        profile = Profile.objects.get(user=user)
        self.assertEqual(str(profile), input_mail)
        self.assertEqual(profile.dark_mode, 'Dark')
        self.assertEqual(profile.theme_color, 'Gray')

        # check that email address object does not exist yet:
        email_address = EmailAddress.objects.get_primary(user)

        with self.assertRaises(AttributeError):
            email_address.email

        # check that email address object is created when saving:
        user.save()
        email_address = EmailAddress.objects.get_primary(user)

        self.assertEqual(email_address.email, input_mail)
        self.assertFalse(email_address.verified)

        # check that the email was changed
        change_mail = 'a@b.com'
        user.email = change_mail
        user.save()
        email_address = EmailAddress.objects.get_primary(user)

        self.assertEqual(email_address.email, change_mail)
        self.assertFalse(email_address.verified)

    @override_settings(OIDC_ADMIN_GROUP='admins', OIDC_GROUPS_CLAIM='groups')
    def test_oidc_handle_admin_rights(self):
        user = User.objects.create_user(username='user', password='12345', email='a@a.com')
        social_account = SocialAccount(
            user=user, provider='dummy_provider', extra_data={'groups': ['admins', 'other_admin']}
        )
        social_login = SocialLogin(account=social_account)

        # assert user is no admin yet
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

        oidc_handle_admin_rights(None, social_login)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    @override_settings(OIDC_ADMIN_GROUP='admins', OIDC_GROUPS_CLAIM='groups')
    def test_oidc_remove_admin_rights(self):
        user = User.objects.create_user(
            username='user', password='12345', email='a@a.com', is_superuser=True, is_staff=True
        )
        social_account = SocialAccount(user=user, provider='dummy_provider', extra_data=dict())
        social_login = SocialLogin(account=social_account)

        # assert user is admin
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

        oidc_handle_admin_rights(None, social_login)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    @override_settings(OIDC_ADMIN_GROUP='admins', OIDC_GROUPS_CLAIM='groups')
    def test_oidc_keep_admin_rights(self):
        user = User.objects.create_user(
            username='user', password='12345', email='a@a.com', is_superuser=True, is_staff=True
        )
        social_account = SocialAccount(user=user, provider='dummy_provider', extra_data={'groups': ['admins']})
        social_login = SocialLogin(account=social_account)

        # assert user is admin
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

        oidc_handle_admin_rights(None, social_login)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    @override_settings(OIDC_ADMIN_GROUP='admins', OIDC_GROUPS_CLAIM='groups')
    def test_oidc_do_not_give_admin_rights(self):
        user = User.objects.create_user(username='user', password='12345', email='a@a.com')
        social_account = SocialAccount(user=user, provider='dummy_provider', extra_data={'groups': ['not_admins']})
        social_login = SocialLogin(account=social_account)

        # assert user is admin
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

        oidc_handle_admin_rights(None, social_login)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    @override_settings(OIDC_ADMIN_GROUP='', OIDC_GROUPS_CLAIM='groups')
    def test_oidc_handle_admin_rights_group_not_set(self):
        user = User.objects.create_user(
            username='user', password='12345', email='a@a.com', is_superuser=True, is_staff=True
        )
        social_account = SocialAccount(user=user, provider='dummy_provider', extra_data={'groups': ['not_admins']})
        social_login = SocialLogin(account=social_account)

        # assert user is admin
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

        #  group is not set so nothing should happen
        oidc_handle_admin_rights(None, social_login)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    @override_settings(OIDC_ADMIN_GROUP='admins', OIDC_GROUPS_CLAIM='groups')
    def test_oidc_handle_admin_right_no_user_exception(self):
        social_account = SocialAccount(user=None, provider='dummy_provider', extra_data={'groups': ['not_admins']})
        social_login = SocialLogin(account=social_account)

        # assert no exception is raised
        oidc_handle_admin_rights(None, social_login)
