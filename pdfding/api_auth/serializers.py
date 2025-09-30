from __future__ import annotations
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from knox.models import AuthToken
from api_auth.models import AccessToken

# Create your serializers here.


def _to_aware(dt):
    # Accept naive datetime; make them aware in current TZ
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


class ReadOnlyAccessTokenSerializer(serializers.ModelSerializer):
    """Read-only serializer for listing and retrieving access tokens."""

    created = serializers.DateTimeField(source="knox_token.created")
    expiry = serializers.DateTimeField(source="knox_token.expiry")
    prefix = serializers.CharField(source="token_key_prefix")

    class Meta:
        model = AccessToken
        fields = ["id", "name", "prefix", "created", "expiry", "last_used"]
        read_only_fields = fields


class BaseAccessTokenSerializer(serializers.ModelSerializer):
    """
    Base serializer for creating and rotating access tokens.
    Handles the `expires_at` field and provides the plaintext token after creation.
    """

    _plaintext_token: str = ""
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = AccessToken
        fields = ("expires_at", "user")

    def to_representation(self, instance: AccessToken):
        return {
            "token": self._plaintext_token,
            "token_key_prefix": instance.token_key_prefix(),
            "id": instance.id, # type: ignore
            "name": instance.name,
            "created": instance.knox_token.created,
            "expiry": instance.knox_token.expiry,
        }


class AccessTokenCreateSerializer(BaseAccessTokenSerializer):
    """
    Creates a new access token (optionally with expires_at) and returns the plaintext token
    """

    def validate_expires_at(self, value):
        if value is None:
            return value
        aware = _to_aware(value)
        now = timezone.now()
        if aware <= now + timedelta(days=1):
            raise serializers.ValidationError("`expires_at` must be in the future.")
        max_expiry = now + timedelta(days=365)
        if aware > max_expiry:
            raise serializers.ValidationError(
                "`expires_at` is too far in the future (max 365 days)."
            )
        return aware

    class Meta:
        model = AccessToken
        fields = BaseAccessTokenSerializer.Meta.fields + ("name",)

    def create(self, validated_data):
        user = validated_data["user"]

        expires_at = validated_data.pop("expires_at", None)
        knox_token, token = create_knox_token(user, expires_at)

        meta = create_access_token(user=user, knox_token=knox_token, name=validated_data["name"])

        self._plaintext_token = token
        return meta


class AccessTokenRotateSerializer(BaseAccessTokenSerializer):
    """
    Rotates (replaces) an existing access token with a new one.
    The old token is deleted. The name and user are preserved.
    """

    def validate_expires_at(self, value):
        if value is None:
            return value
        aware = _to_aware(value)
        if aware <= timezone.now():
            raise serializers.ValidationError("expires_at must be in the future.")
        return aware

    def update(self, instance: AccessToken, validated_data: dict) -> AccessToken:
        user = self.context["request"].user
        if validated_data["user"].id != user.id:
            raise serializers.ValidationError("Not allowed to rotate this token.")

        instance.knox_token.delete()
        expires_at = validated_data.get("expires_at", None)  # type: ignore
        knox_token, token = create_knox_token(user, expires_at)

        new_meta = create_access_token(user=user, knox_token=knox_token, name=instance.name)
        self._plaintext_token = token
        return new_meta


def create_access_token(user, knox_token, name):
    return AccessToken.objects.create(user=user, knox_token=knox_token, name=name)


def create_knox_token(user, expires_at) -> tuple[AuthToken, str]:
    """ Creates a new Knox AuthToken for the given user with optional expiry."""

    return AuthToken.objects.create(user=user, expiry=expires_at)  # type: ignore
