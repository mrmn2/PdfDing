import pytest
from api.models import AccessToken
from django.urls import reverse
from knox.models import AuthToken
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


class TestAccessTokenView:

    def test_permissions_required(self):
        url = reverse("api_token_detail", args=[1])
        client = APIClient()
        response = client.patch(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED  # type: ignore

    def test_token_update(self, api_client, token):
        url = reverse("api_token_detail", args=[token.id])
        data = {"name": "Updated Token Name"}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Token Name"

    def test_token_update_other_user_forbidden(self, api_client, another_user):
        knox_token: [AuthToken, str] = AuthToken.objects.create(user=another_user)  # type: ignore
        other_token = AccessToken.objects.create(user=another_user, name="MyAPIToken", knox_token=knox_token[0])

        url = reverse("api_token_detail", args=[other_token.id])  # type: ignore
        data = {"name": "Hacked Token Name"}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_404_NOT_FOUND  # should not reveal existence
