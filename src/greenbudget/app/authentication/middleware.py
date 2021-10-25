from django.conf import settings
from django.contrib import auth
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from django.utils.http import http_date

from rest_framework_simplejwt.settings import api_settings

from .tokens import AuthToken
from .exceptions import InvalidToken
from .utils import parse_token_from_request, parse_token


def user_can_proceed(user):
    return user.is_authenticated and user.is_verified and user.is_approved


def get_user(request):
    if not hasattr(request, '_cached_user'):
        user = auth.get_user(request)
        if user_can_proceed(user) and user.stripe_id is not None:
            raw_token = parse_token_from_request(request)
            _, token_obj = parse_token(raw_token, api_context=True)
            # Use the JWT token to prepopulate billing related values on the
            # user to avoid unnecessary requests to Stripe's API.
            user.cache_stripe_from_token(token_obj)
        request._cached_user = user
        # Both middlewares present here are concerned with the user that is
        # parsed from the JWT token.  Since obtaining the user from the JWT
        # token involves a DB query, we want to set the result on the request
        # so that subsequent middlewares can access the same result without
        # having to re-parse the JWT token and make an additional DB query.
        request._parsed_token_user = user
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
        request.user = SimpleLazyObject(lambda: get_user(request))


def get_cookie_user(request):
    # We only want to use the session user in the case that we are not in the
    # process of validating the JWT authentication token.
    is_validate_url = request.path == reverse('authentication:validate')
    if not hasattr(request, '_cached_cookie_user'):
        request_user = getattr(request, 'user', None)
        if request_user and user_can_proceed(request_user) \
                and not is_validate_url:
            request._cached_cookie_user = request.user
        else:
            # If the token was already parsed from the previous middleware
            # (AuthenticationBillingMiddleware), we do not want to reparse the
            # token and obtain the user because it involves an extra DB query.
            #
            # Since we accessed a property on request.user (in the first
            # conditional to check if the user can proceed), the lazy evaluated
            # `get_user` method will have been called, which means the
            # `parsed_token_user` attribute should be on the request.
            if hasattr(request, '_parsed_token_user'):
                request._cached_cookie_user = request._parsed_token_user
            else:
                raw_token = parse_token_from_request(request)
                request._cached_cookie_user, _ = parse_token(
                    raw_token, api_context=True)

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
        # In some cases, the request will be a WSGIRequest object - this happens
        # during tests.
        if hasattr(request, 'session'):
            auth.logout(request)
        return self.delete_cookie(response)

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
        is_validate_url = request.path == reverse('authentication:validate')

        is_write_method = request.method not in ('GET', 'HEAD', 'OPTIONS')
        is_admin = '/admin/' in request.path
        return not is_admin and (
            is_missing_jwt or is_write_method or is_validate_url)

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
                    or not request.cookie_user.is_approved \
                    or force_logout is True:
                return self.force_logout(request, response)

        if self.should_persist_cookie(request):
            self.persist_cookie(request, response)
        return response
