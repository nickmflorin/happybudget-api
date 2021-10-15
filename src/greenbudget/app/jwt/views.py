from django.utils.translation import ugettext_lazy as _

from rest_framework import status, response, views

from greenbudget.app.authentication.auth_backends import (
    CsrfExcemptCookieSessionAuthentication)
from greenbudget.app.user.serializers import UserSerializer

from .serializers import UserTokenRefreshSerializer, parse_token_from_request


class TokenRefreshView(views.APIView):
    authentication_classes = (CsrfExcemptCookieSessionAuthentication, )

    def get(self, request, *args, **kwargs):
        return response.Response({
            "detail": _("Successfully refreshed token."),
        }, status=status.HTTP_200_OK)


class TokenValidateView(views.APIView):
    authentication_classes = (CsrfExcemptCookieSessionAuthentication, )

    def post(self, request, *args, **kwargs):
        token = parse_token_from_request(request)
        serializer = UserTokenRefreshSerializer(force_logout=True)
        user, _ = serializer.validate({"token": token})
        return response.Response({
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
