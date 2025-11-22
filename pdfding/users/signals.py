from allauth.account.models import EmailAddress
from allauth.socialaccount.signals import pre_social_login
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def user_postsave(sender, instance, created, **kwargs):
    """Create the corresponding django user if a profile is created."""

    user = instance

    # add profile if user is created
    if created:
        profile = Profile.objects.create(user=user)
        profile.dark_mode = Profile.DarkMode[str.upper(settings.DEFAULT_THEME)]
        profile.theme_color = Profile.ThemeColor[str.upper(settings.DEFAULT_THEME_COLOR)]
        profile.current_workspace_id = user.id
        profile.current_collection_id = user.id
        profile.save()

    # user email address was changed -> set it to unverified
    else:
        # update allauth emailaddress if exists
        try:
            email_address = EmailAddress.objects.get_primary(user)
            if email_address.email != user.email:
                email_address.email = user.email
                email_address.verified = False
                email_address.save()
        except AttributeError:
            # if allauth emailaddress doesn't exist create one
            EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=False)


@receiver(pre_social_login)
def oidc_handle_admin_rights(request, sociallogin, **kwargs):
    """
    Use the pre_social_login signal to add admin rights based on the oidc groups claim.

    Sent after a user successfully authenticates via a social provider, but before the login is fully processed.
    This signal is emitted as part of the social login and/or signup process, as well as when connecting additional
    social accounts to an existing account.
    """

    # we need a try except statement as the user is not existing when loging in the first time via oidc
    try:
        if settings.OIDC_ADMIN_GROUP:
            user = sociallogin.account.user
            groups = sociallogin.account.extra_data.get(settings.OIDC_GROUPS_CLAIM, [])

            if settings.OIDC_ADMIN_GROUP in groups and not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                user.save()
            elif settings.OIDC_ADMIN_GROUP not in groups and user.is_superuser:
                user.is_staff = False
                user.is_superuser = False
                user.save()
    except ObjectDoesNotExist:
        pass
