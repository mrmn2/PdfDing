from unittest.mock import patch

from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from users.adapters import HandleAdminNewUserAdapter


class TestAdapters(TestCase):
    @patch('users.adapters.DefaultSocialAccountAdapter.new_user')
    @override_settings(OIDC_ADMIN_GROUP='admins', OIDC_GROUPS_CLAIM='groups')
    def test_new_user_create_admin_user(self, mock_super_new_user):
        user = User.objects.create_user(username='user', password='12345', email='a@a.com')
        social_account = SocialAccount(user=user, provider='dummy_provider', extra_data={'groups': ['admins']})
        social_login = SocialLogin(account=social_account)
        mock_super_new_user.return_value = user

        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

        adapter = HandleAdminNewUserAdapter()
        user = adapter.new_user(None, social_login)

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    @patch('users.adapters.DefaultSocialAccountAdapter.new_user')
    @override_settings(OIDC_ADMIN_GROUP='admins', OIDC_GROUPS_CLAIM='groups')
    def test_new_user_no_admin_user(self, mock_super_new_user):
        user = User.objects.create_user(username='user', password='12345', email='a@a.com')
        social_account = SocialAccount(user=user, provider='dummy_provider', extra_data={'groups': ['non_admins']})
        social_login = SocialLogin(account=social_account)
        mock_super_new_user.return_value = user

        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

        adapter = HandleAdminNewUserAdapter()
        user = adapter.new_user(None, social_login)

        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
