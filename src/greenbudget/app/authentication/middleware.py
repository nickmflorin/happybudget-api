import logging

from django.conf import settings
from django.contrib.auth import logout
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from django.utils.http import http_date

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError

from .tokens import SlidingToken
from .exceptions import (
    ExpiredToken, InvalidToken, TokenExpiredError, TokenCorruptedError)
from .utils import get_user_from_token, parse_token_from_request


logger = logging.getLogger('backend')


def get_cookie_user(request):
    if not hasattr(request, '_cached_cookie_user'):
        user = getattr(request, 'user', None)
        if user and user.is_active and user.is_verified:
            request._cached_cookie_user = user
        else:
            # If there is no token on the request, the user will be the
            # AnonymousUser() instance.
            raw_token = parse_token_from_request(request)
            try:
                request._cached_cookie_user, _ = get_user_from_token(
                    raw_token)
            except TokenCorruptedError as e:
                logger.info("The provided token is corrupted.")
                raise InvalidToken(*e.args) from e
            except TokenExpiredError as e:
                logger.info("The provided token has expired.")
                raise ExpiredToken(*e.args) from e
            except TokenError as e:
                logger.info("The provided token is invalid.")
                raise InvalidToken(*e.args) from e

    return request._cached_cookie_user


class TokenCookieMiddleware(MiddlewareMixin):
    """
    Middleware that automatically maintains a :obj:`User`'s authenticated
    state using cookies for JWT authentication.
    """
    cookie_kwargs = {
        'domain': getattr(settings, 'JWT_COOKIE_DOMAIN', None) or None,
        'path': '/',
    }

    def __init__(self, get_response=None):
        self.get_response = get_response

    def force_logout(self, request, response, **kwargs):
        # In some cases, the request will be a WSGIRequest object - this happens
        # during tests.
        if hasattr(request, 'session'):
            logout(request)

        # Browsers don't actually delete the cookie, they simply set the
        # cookie expiration date to a date in the past.  If the parameters
        # used to set the cookie are not the same as those used to delete
        # the cookie, the Browser cannot do this.
        response.delete_cookie(
            settings.JWT_TOKEN_COOKIE_NAME, **self.cookie_kwargs)

        # Update the response body to include information informing the FE to
        # potentially forcefully log the user out.  Note that in the case that
        # there is a server error, the response object is HttpResponseServerError
        # which does not have a `data` attribute.
        if hasattr(response, 'data'):
            response.data.update(
                dict((k, v) for k, v in kwargs.items() if v is not None))

            # Include a `force_logout` attribute in the response to inform the FE
            # that we need to forcefully log the user out.
            response.data.update(force_logout=True)

            # If an Exception was raised that caused the rendered response
            # includes a `user_id` attribute, that parameter will be set on the
            # response object.  We need to include that value in the top level
            # of the response for the FE.
            if getattr(response, '_user_id', None) is not None:
                response.data.update(user_id=getattr(response, '_user_id'))

            response._is_rendered = False
            response.render()
        return response

    def should_persist_cookie(self, request):
        """
        The JWT cookie should be persisted if the request is not coming from the
        Admin hosted site and either of the following conditions are met:

        (1) The :obj:`Request` does not already have the JWT token in it's
            cookies.
        (2) The :obj:`Request` pertains to a POST, PATCH, PUT or DELETE method.
        (3) The :obj:`Request` pertains to a request to refresh the JWT token.
        (4) The :obj:`Request` pertains to a request to validate the JWT token.
        """
        is_missing_jwt = settings.JWT_TOKEN_COOKIE_NAME not in request.COOKIES
        is_refresh_url = request.path == reverse('authentication:refresh')
        is_validate_url = request.path == reverse('authentication:validate')

        is_write_method = request.method not in ('GET', 'HEAD', 'OPTIONS')
        is_admin = '/admin/' in request.path
        return not is_admin and (
            is_missing_jwt or is_write_method or is_refresh_url or is_validate_url)  # noqa

    def persist_cookie(self, request, response):
        """
        Persists the JWT token in the cookies of the :obj:`response.Response`
        if the :obj:`User` is authenticated and the conditions dictated by
        the `should_persist_cookie` method indicate that it should be persisted.
        """
        if self.should_persist_cookie(request):
            token = SlidingToken.for_user(request.cookie_user)
            expires = http_date(
                token[api_settings.SLIDING_TOKEN_REFRESH_EXP_CLAIM])
            response.set_cookie(
                settings.JWT_TOKEN_COOKIE_NAME,
                str(token),
                expires=expires,
                secure=settings.JWT_COOKIE_SECURE or None,
                **self.cookie_kwargs,
                httponly=False,
                samesite=False
            )
        return response

    def process_request(self, request):
        assert hasattr(settings, 'JWT_TOKEN_COOKIE_NAME'), (
            'TokenCookieMiddleware requires the '
            'JWT_TOKEN_COOKIE_NAME setting to be set')
        request.cookie_user = SimpleLazyObject(lambda: get_cookie_user(request))

    def process_response(self, request, response):
        is_logout_url = request.path == reverse('authentication:logout')
        try:
            is_active = request.cookie_user and request.cookie_user.is_active
        except InvalidToken:
            return self.force_logout(request, response)
        else:
            if is_logout_url:
                return response
            # The response will have a `_force_logout` attribute if the
            # Exception that was raised to trigger the response had a
            # `force_logout` attribute that evalutes to True.
            force_logout = getattr(response, '_force_logout', None)
            if not is_active or not request.cookie_user.is_verified \
                    or force_logout is True:
                if force_logout:
                    return self.force_logout(
                        request, response, user_id=request.cookie_user.pk)
                elif hasattr(response, 'data') \
                        and getattr(response, '_user_id', None) is not None:
                    response.data.update(user_id=getattr(response, '_user_id'))
                return response

        return self.persist_cookie(request, response)
