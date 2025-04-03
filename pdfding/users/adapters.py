from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class DisableSignupAccountAdapter(DefaultAccountAdapter):
    """Adapter for disabling user signup depending on the SIGNUP_CLOSED setting."""

    def is_open_for_signup(self, request):
        """Disable user signup depending on the SIGNUP_CLOSED setting."""

        return not settings.SIGNUP_CLOSED


class HandleAdminNewUserAdapter(DefaultSocialAccountAdapter):
    def new_user(self, request, sociallogin):
        """When creating a new user via oidc, add admin rights based on the oidc groups claim"""

        user = super().new_user(request, sociallogin)

        if settings.OIDC_ADMIN_GROUP:
            groups = sociallogin.account.extra_data.get(settings.OIDC_GROUPS_CLAIM, [])

            if settings.OIDC_ADMIN_GROUP in groups:
                user.is_staff = True
                user.is_superuser = True

        return user
