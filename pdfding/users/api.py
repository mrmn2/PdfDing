from rest_framework import serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ['key', 'created']


class TokenViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    serializer_class = TokenSerializer

    def list(self, request):
        token = Token.objects.filter(user=request.user).first()
        return Response({'token': token}, template_name='partials/token_management.html')

    def create(self, request):
        token, created = Token.objects.get_or_create(user=request.user)
        return Response({'token': token}, template_name='partials/token_management.html', status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='rotate')
    def rotate(self, request):
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        return Response({'token': token}, template_name='partials/token_management.html')

    @action(detail=False, methods=['post'], url_path='delete')
    def delete(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({'token': None}, template_name='partials/token_management.html')
