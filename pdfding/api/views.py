from api.models import AccessToken
from api.serializers import AccessTokenUpdateSerializer
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated

# Create your views here.


class AccessTokenView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AccessTokenUpdateSerializer
    queryset = AccessToken.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
