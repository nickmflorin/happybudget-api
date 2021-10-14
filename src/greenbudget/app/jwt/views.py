from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from greenbudget.app.user.serializers import UserSerializer

from .auth_backends import (
    JWTCookieAuthentication, CsrfExcemptSessionAuthentication)
from .serializers import UserTokenSlidingSerializer


class TokenRefreshView(APIView):
    authentication_classes = (
        CsrfExcemptSessionAuthentication, JWTCookieAuthentication)

    def get(self, request, *args, **kwargs):
        return Response({
            "detail": _("Successfully refreshed token."),
        }, status=status.HTTP_200_OK)


class TokenValidateView(APIView):
    authentication_classes = (
        JWTCookieAuthentication, CsrfExcemptSessionAuthentication, )

    def post(self, request, *args, **kwargs):
        token = request.COOKIES.get(settings.JWT_TOKEN_COOKIE_NAME)
        serializer = UserTokenSlidingSerializer()
        user = serializer.validate({"token": token})
        return Response({
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
