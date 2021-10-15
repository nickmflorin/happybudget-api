from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from rest_framework import authentication

from .exceptions import (
    EmailNotVerified, AccountDisabledError, EmailDoesNotExist,
    InvalidCredentialsError)


def user_can_log_in(user, force_logout=False, raise_exception=False):
    if not user.is_active:
        if raise_exception:
            raise AccountDisabledError(
                user_id=user.pk,
                force_logout=force_logout
            )
        return False
    elif not user.is_verified:
        if raise_exception:
            raise EmailNotVerified(
                user_id=user.pk,
                force_logout=force_logout
            )
        return False
    return True


def validate_if_user_can_log_in(user, force_logout=False):
    user_can_log_in(user, force_logout=force_logout, raise_exception=True)


class ModelAuthentication(ModelBackend):
    def authenticate(self, *args, **kwargs):
        force_logout = kwargs.pop('force_logout', None)
        user = kwargs.pop('user', None)
        if user is None:
            if 'token_id' in kwargs and 'provider' in kwargs:
                return self.authenticate_with_social(
                    token_id=kwargs['token_id'],
                    provider=kwargs['provider'],
                    force_logout=force_logout
                )
            email = kwargs.pop(get_user_model().USERNAME_FIELD)
            try:
                user = get_user_model()._default_manager.get_by_natural_key(email)  # noqa
            except get_user_model().DoesNotExist:
                raise EmailDoesNotExist('email')

        password = kwargs.pop('password')
        if not user.check_password(password):
            raise InvalidCredentialsError("password")
        validate_if_user_can_log_in(user, force_logout=force_logout)
        return user

    def authenticate_with_social(self, token_id, provider, force_logout=None):
        user = get_user_model().objects.get_or_create_from_social_token(
            token_id=token_id,
            provider=provider
        )
        validate_if_user_can_log_in(user, force_logout=force_logout)
        return user


class SessionAuthentication(authentication.SessionAuthentication):
    """
    An extension of :obj:`rest_framework.authentication.SessionAuthentication`
    that prevents :obj:`User`(s) with unverified email addresses from logging
    in.
    """

    def get_user(self, request):
        return getattr(request._request, 'user', None)

    def authenticate(self, request):
        user = self.get_user(request)
        # Unauthenticated, CSRF validation not required
        if not user or not user.is_active:
            return None
        self.enforce_csrf(request)
        if not user.is_verified:
            return None
        # CSRF passed with authenticated user
        return (user, None)


class CookieSessionAuthentication(SessionAuthentication):
    """
    An extension of :obj:`greenbudget.app.authentication.SessionAuthentication`
    that authenticates the :obj:`User` associated with the JWT token.
    """

    def get_user(self, request):
        return getattr(request._request, 'cookie_user', None)


class CsrfExcemptCookieSessionAuthentication(CookieSessionAuthentication):
    """
    An extension of `greenbudget.app.authentication.CookieSessionAuthentication`
    that does not enforce CSRF checks.  This is required for views related to
    JWT token validation.

    Django REST Framework basically prevents the CSRFViewMiddleware from
    being used by decorating any API View with @csrf_excempt, and instead it
    explicitly performs the CSRF check when a user is authenticated via
    `rest_framework.authentication.SessionAuthentication` - so decorating
    the JWT views with @csrf_excempt does nothing.

    The solution is not to remove the Session Authentication from those views,
    but to instead extend it so that it still performs Session Authentication,
    but does not enforce the CSRF check.
    """

    def authenticate(self, request):
        user = self.get_user(request)
        if not user or not user_can_log_in(user):
            return None
        return (user, None)
