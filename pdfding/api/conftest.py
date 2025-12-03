from uuid import uuid4

import pytest
from api.models import AccessToken
from django.contrib.auth import get_user_model
from knox.models import AuthToken


@pytest.fixture
def user():
    return get_user_model().objects.create_user(username="testuser", password=uuid4().hex)


@pytest.fixture
def another_user():
    return get_user_model().objects.create_user(username="anotheruser", password=uuid4().hex)


@pytest.fixture
def knox_token(user) -> tuple[AuthToken, str]:
    return AuthToken.objects.create(user=user)  # type: ignore


@pytest.fixture
def token(knox_token):
    return AccessToken.objects.create(user=knox_token[0].user, name="MyAPIToken", knox_token=knox_token[0])
