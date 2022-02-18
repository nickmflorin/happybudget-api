import logging

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from django.utils.http import http_date

from rest_framework_simplejwt.settings import api_settings

from greenbudget.conf import Environments

from .exceptions import InvalidToken
from .tokens import AuthToken
from .utils import (
    parse_token_from_request, parse_token, user_can_authenticate,
    request_is_admin, request_is_write_method, parse_public_token)


logger = logging.getLogger('greenbudget')


def get_public_token(request):
    if not hasattr(request, '_cached_public_token'):
        request._cached_public_token = parse_public_token(request=request)
    return request._cached_public_token


class PublicTokenMiddleware(MiddlewareMixin):
    """
    Middleware that automatically maintains a public token on the request,
    as it is provided via the the request header defined by the settings
    configuration `PUBLIC_TOKEN_HEADER`.
    """

    def process_request(self, request):
        assert hasattr(settings, 'PUBLIC_TOKEN_HEADER'), \
            'PublicTokenMiddleware requires the PUBLIC_TOKEN_HEADER setting ' \
            'to be set.'
        request.public_token = SimpleLazyObject(
            lambda: get_public_token(request))


def get_session_user(request, cache_stripe_info=True):
    if not hasattr(request, '_cached_user'):
        session_user = auth.get_user(request)
        if user_can_authenticate(session_user, raise_exception=False) \
                and session_user.stripe_id is not None \
                and cache_stripe_info:
            raw_token = parse_token_from_request(request)
            # Store the cached cookie user for subsequent middlewares so we
            # can avoid parsing the token multiple times (since it involves
            # a DB query).
            token_user, token_obj = parse_token(raw_token)
            # Use the JWT token to prepopulate billing related values on the
            # user to avoid unnecessary requests to Stripe's API.
            session_user.cache_stripe_from_token(token_obj)
            # We want to also prepopulate billing related values on the token
            # user so that the JWT authentication token validation view does
            # not make repetitive requests to Stripe's API.
            token_user.cache_stripe_from_token(token_obj)
            # Store the cached cookie user for subsequent middlewares so we
            # can avoid parsing the token multiple times (since it involves
            # a DB query).
            request._cached_cookie_user = token_user
        request._cached_user = session_user
    return request._cached_user


class BillingTokenCookieMiddleware(AuthenticationMiddleware):
    """
    Middleware that automatically maintains a :obj:`User`'s billing status
    using JWT tokens stored in cookies.  The JWT tokens contain billing
    information about the user which we can use to avoid unnecessary and
    redundant requests to Stripe's API.
    """

    def process_request(self, request):
        if not hasattr(request, 'session'):
            return super().process_request(request)
        request.user = SimpleLazyObject(lambda: get_session_user(request))


def get_cookie_user(request):
    # We only want to use the session user in the case that we are not in the
    # process of validating the JWT authentication token.
    is_validate_url = request.path == reverse('authentication:validate')
    if not hasattr(request, '_cached_cookie_user'):
        request._cached_cookie_user = AnonymousUser()
        # If the session user is not authenticated, we do not want to allow the
        # token validation endpoints to return the user based on the JWT token.
        session_user = getattr(request, 'user', None)
        if session_user \
                and user_can_authenticate(session_user, raise_exception=False):
            if not is_validate_url:
                request._cached_cookie_user = session_user
            else:
                raw_token = parse_token_from_request(request)
                token_user, token_obj = parse_token(raw_token)
                if user_can_authenticate(token_user, raise_exception=False):
                    # We want to also prepopulate billing related values on the
                    # token user so that the JWT authentication token validation
                    # view does not make repetitive requests to Stripe's API.
                    token_user.cache_stripe_from_token(token_obj)
                    request._cached_cookie_user = token_user
    return request._cached_cookie_user


class AuthTokenCookieMiddleware(MiddlewareMixin):
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

    @classmethod
    def delete_cookie(cls, response):
        # Browsers don't actually delete the cookie, they simply set the
        # cookie expiration date to a date in the past.  If the parameters
        # used to set the cookie are not the same as those used to delete
        # the cookie, the Browser cannot do this.
        if settings.JWT_TOKEN_COOKIE_NAME in response.cookies:
            response.delete_cookie(
                settings.JWT_TOKEN_COOKIE_NAME, **cls.cookie_kwargs)
        return response

    def force_logout(self, request, response):
        # In tests, using RequestFactory, there will be no session on the
        # request.
        if settings.ENVIRONMENT != Environments.TEST:
            auth.logout(request)
        return self.delete_cookie(response, **self.cookie_kwargs)

    def should_persist_cookie(self, request, response):
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
        is_validate_url = request.path == reverse('authentication:validate')
        return not request_is_admin(request) and response.status_code != 401 \
            and (is_missing_jwt or request_is_write_method(request)
            or is_validate_url)

    def persist_cookie(self, request, response):
        """
        Persists the JWT token in the cookies of the :obj:`response.Response`
        if the :obj:`User` is authenticated and the conditions dictated by
        the `should_persist_cookie` method indicate that it should be persisted.
        """
        token = AuthToken.for_user(request.cookie_user)
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

    def process_request(self, request):
        assert hasattr(settings, 'JWT_TOKEN_COOKIE_NAME'), (
            'TokenCookieMiddleware requires the '
            'JWT_TOKEN_COOKIE_NAME setting to be set')
        request.cookie_user = SimpleLazyObject(lambda: get_cookie_user(request))

    def process_response(self, request, response):
        is_logout_url = request.path == reverse('authentication:logout')
        try:
            is_authenticated = request.cookie_user \
                and request.cookie_user.is_authenticated
        except InvalidToken:
            # If the JWT token stored in cookies is invalid or missing, remove
            # the user's session and delete the JWT token from the response.
            return self.force_logout(request, response)
        else:
            if is_logout_url:
                return response

            # If the user dictated by the JWT token is either not authenticated,
            # not active or not verified, remove the user's session and delete
            # the JWT token from the response.
            if not is_authenticated or not request.cookie_user.is_active \
                    or not request.cookie_user.email_is_verified:
                return self.force_logout(request, response)

            # For security purposes, we need to make sure that the user dictated
            # by Django's session is the same user that is dictated by the JWT
            # token.  If they are not, we need to remove the session and delete
            # the JWT token from the response, as this is indicative of a
            # malicious attempt to exploit potential security holes.
            if settings.ENVIRONMENT != Environments.TEST:
                session_user = get_session_user(request, cache_stripe_info=False)
                if session_user != request.cookie_user \
                        and session_user.is_authenticated:
                    logger.error(
                        "Session Authentication & JWT Cookie Authentication "
                        "are indicating different users!  This is a sign "
                        "that someone may be trying to exploit a security "
                        "hole!", extra={
                            'token_user':
                            getattr(request.cookie_user, 'pk', None),
                            'session_user':
                            getattr(session_user, 'pk', None),
                            'request': request
                        }
                    )
                    return self.force_logout(request, response)

        if self.should_persist_cookie(request, response):
            self.persist_cookie(request, response)
        return response
