from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from greenbudget.app.user.serializers import UserSerializer

from .auth_backends import (
    JWTCookieAuthentication, CsrfExcemptSessionAuthentication)
from .exceptions import InvalidToken, ExpiredToken, TokenExpiredError
from .utils import verify_token


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
        try:
            token_obj = verify_token(token)
        except TokenExpiredError as e:
            raise ExpiredToken(*e.args) from e
        except TokenError as e:
            raise InvalidToken(*e.args) from e
        user_id = token_obj.get(api_settings.USER_ID_CLAIM)
        user = get_user_model().objects.get(pk=user_id)
        return Response({
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
