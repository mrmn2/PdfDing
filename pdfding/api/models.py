from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.db import models
from knox.models import AuthToken

# Create your models here.


User = get_user_model()


class AccessToken(models.Model):
    """
    Model representing an access token associated with a user.
    """

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="access_tokens")
    name = models.CharField(
        verbose_name="Token Name",
        max_length=64,
        validators=[
            MinLengthValidator(3),
        ],
    )
    knox_token = models.OneToOneField(to=AuthToken, on_delete=models.CASCADE, related_name="meta")

    last_used = models.DateTimeField(blank=True, null=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Access Token"
        verbose_name_plural = "Access Tokens"
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="unique_token_name_per_user"),
        ]

    def __str__(self) -> str:
        return self.name

    def token_key_prefix(self) -> str:
        # show first 8 chars of token key (safe identifier)
        return self.knox_token.token_key[:8]
