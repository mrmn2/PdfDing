import pytest
from api.models import AccessToken

# Create your tests here.
pytestmark = pytest.mark.django_db


class TestAccessTokenModel:

    def test_access_token_creation(self, user, knox_token):
        token = AccessToken.objects.create(user=user, name="MyToken", knox_token=knox_token[0])
        assert token.user == user
        assert token.name == "MyToken"
        assert token.knox_token == knox_token[0]
        assert token.last_used is None
        assert str(token) == "MyToken"

    def test_token_key_prefix(self, knox_token, user):
        token = AccessToken.objects.create(user=user, name="Test Token", knox_token=knox_token[0])
        prefix = token.token_key_prefix()
        assert isinstance(prefix, str)
        assert len(prefix) == 8
        assert prefix == knox_token[0].token_key[:8]
