from django.dispatch import receiver
from django.db.models.signals import post_save
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from .models import Profile


@receiver(post_save, sender=User)
def user_postsave(sender, instance, created, **kwargs):
    """Create the corresponding django user if a profile is created."""

    user = instance

    # add profile if user is created
    if created:
        Profile.objects.create(
            user=user,
        )
    else:
        email_address = EmailAddress.objects.get_primary(user)
        if email_address.email != user.email:
            email_address.email = user.email
            email_address.verified = False
            email_address.save()
