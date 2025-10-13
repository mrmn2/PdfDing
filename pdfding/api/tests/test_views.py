from django.utils import timezone
import pytest
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
from api.models import AccessToken

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


class TestAccessTokenViewSet:

    def test_permissions_required(self):
        url = reverse("api_tokens-list")
        client = APIClient()
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED  # type: ignore

    def test_token_creation(self, api_client):
        url = reverse("api_tokens-list")
        data = {"name": "Test Token"}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert "token" in response.data
        assert response.data["name"] == "Test Token"

    def test_token_cant_be_accessed_after_creation(self, api_client):
        url = reverse("api_tokens-list")
        data = {"name": "Test Token"}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert "token" in response.data

        url = reverse("api_tokens-detail", args=[response.data["id"]])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Token"

        # token should not be retrievable
        assert "token" not in response.data

    def test_token_creation_fail_expiry_in_past(self, api_client):
        url = reverse("api_tokens-list")
        data = {"name": "Test Token", "expires_at": timezone.now() - timezone.timedelta(days=1)}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_token_creation_fail_expiry_more_than_365_days_in_future(self, api_client):
        url = reverse("api_tokens-list")
        data = {"name": "Test Token", "expires_at": timezone.now() + timezone.timedelta(days=366)}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_token_deletion(self, api_client, token):
        url = reverse("api_tokens-detail", args=[token.id])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert AccessToken.objects.filter(id=token.id).exists() is False

        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_token_rotation(self, api_client, token):
        url = reverse("api_tokens-rotate", args=[token.id])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        assert "token" in response.data
        assert response.data["id"] != token.id
        assert AccessToken.objects.filter(id=response.data["id"]).exists()
