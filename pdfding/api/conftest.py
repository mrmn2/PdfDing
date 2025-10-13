from django.contrib.auth import get_user_model

from knox.models import AuthToken
import pytest

from api.models import AccessToken


@pytest.fixture
def user():
    return get_user_model().objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def knox_token(user) -> tuple[AuthToken, str]:
    return AuthToken.objects.create(user=user)  # type: ignore


@pytest.fixture
def token(knox_token):
    return AccessToken.objects.create(user=knox_token[0].user, name="MyAPIToken", knox_token=knox_token[0])
