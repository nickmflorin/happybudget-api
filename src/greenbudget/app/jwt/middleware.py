import logging

from django.conf import settings
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from django.utils.http import http_date

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError

from .tokens import GreenbudgetSlidingToken
from .exceptions import ExpiredToken, InvalidToken, TokenExpiredError
from .serializers import get_user_from_token, parse_token_from_request


logger = logging.getLogger('backend')


def get_cookie_user(request):
    if not hasattr(request, '_cached_cookie_user'):
        if getattr(request, 'user', None) and request.user.is_active:
            request._cached_cookie_user = request.user
        else:
            raw_token = parse_token_from_request(request)
            try:
                request._cached_cookie_user = get_user_from_token(raw_token)
            except TokenExpiredError as e:
                logger.info("The provided token has expired.")
                raise ExpiredToken(*e.args) from e
            except TokenError as e:
                logger.info("The provided token is invalid.")
                raise InvalidToken(*e.args) from e
    return request._cached_cookie_user


class TokenCookieMiddleware(MiddlewareMixin):
    """
    Middleware that automatically maintains and uses cookies for JWT
    authentication.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_request(self, request):
        assert hasattr(settings, 'JWT_TOKEN_COOKIE_NAME'), (
            'TokenCookieMiddleware requires the '
            'JWT_TOKEN_COOKIE_NAME setting to be set')
        request.cookie_user = SimpleLazyObject(lambda: get_cookie_user(request))

    def process_response(self, request, response):
        cookie_kwargs = {
            'domain': getattr(settings, 'JWT_COOKIE_DOMAIN', None) or None,
            'path': '/',
        }
        set_cookie_kwargs = dict(
            cookie_kwargs,
            secure=settings.JWT_COOKIE_SECURE or None,
            httponly=False,
            samesite=False
        )
        try:
            is_active = request.cookie_user and request.cookie_user.is_active
        except InvalidToken:
            response.delete_cookie(
                settings.JWT_TOKEN_COOKIE_NAME, **cookie_kwargs)
            return response
        else:
            if not is_active or not request.cookie_user.is_verified:
                return response

        # Update the JWT if the user is requesting the JWT refresh URL, the JWT
        # validate URL or the request isn't using a "read only" HTTP method
        is_missing_jwt = settings.JWT_TOKEN_COOKIE_NAME not in request.COOKIES
        is_refresh_url = request.path == reverse('jwt:refresh')
        is_validate_url = request.path == reverse('jwt:validate')
        is_write_method = request.method not in ('GET', 'HEAD', 'OPTIONS')
        is_admin = '/admin/' in request.path
        if not is_admin and (
                is_missing_jwt or is_write_method or is_refresh_url
                or is_validate_url):
            token = GreenbudgetSlidingToken.for_user(request.cookie_user)
            expires = http_date(
                token[api_settings.SLIDING_TOKEN_REFRESH_EXP_CLAIM])
            response.set_cookie(
                settings.JWT_TOKEN_COOKIE_NAME,
                str(token),
                expires=expires,
                **set_cookie_kwargs
            )
        return response
