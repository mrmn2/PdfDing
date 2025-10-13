from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.models import AccessToken
from api.serializers import (
    AccessTokenCreateSerializer,
    AccessTokenRotateSerializer,
    ReadOnlyAccessTokenSerializer,
)

# Create your views here.


class AccessTokenViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = AccessToken.objects.select_related("knox_token")

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_serializer_class(self):

        if self.action == "create":
            ser = AccessTokenCreateSerializer
        elif self.action == "rotate":
            ser = AccessTokenRotateSerializer
        else:
            ser = ReadOnlyAccessTokenSerializer

        return ser

    @action(methods=["POST"], detail=True)
    def rotate(self, request, pk=None):
        meta = self.get_object()
        serializer = self.get_serializer(instance=meta, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)
