import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from rest_framework import authentication

from .exceptions import (
    InvalidCredentialsError, EmailDoesNotExist, NotAuthenticatedError)
from .utils import user_can_authenticate


logger = logging.getLogger('greenbudget')


class SocialModelAuthentication(ModelBackend):
    """
    An extension of :obj:`django.contrib.auth.backends.ModelBackend` that
    allows users to be authenticated from social login.
    """

    def authenticate(self, request, token_id=None, provider=None):
        if token_id is not None and provider is not None:
            user = get_user_model().objects.get_or_create_from_social_token(
                token_id=token_id,
                provider=provider
            )
            return user_can_authenticate(user)
        return None


class ModelAuthentication(ModelBackend):
    """
    An extension of :obj:`django.contrib.auth.backends.ModelBackend` that
    enforces that a user has a verified email address before allowing them
    to fully login.
    """

    def authenticate(self, request, username=None, email=None, password=None):
        # When logging in from the Django Admin, it will pass the value in as
        # the username.
        email = email or username
        is_admin = '/admin/' in request.path
        if email is not None and password is not None:
            try:
                user = get_user_model().objects.get(email=email)
            except get_user_model().DoesNotExist:
                # If we are coming from the Admin, we do not want to raise a
                # DRF exception as it will not render in the response, it will
                # just be a 500 error.
                if not is_admin:
                    raise EmailDoesNotExist('email')
                return None
            if not user.check_password(password):
                # If we are coming from the Admin, we do not want to raise a
                # DRF exception as it will not render in the response, it will
                # just be a 500 error.
                if not is_admin:
                    raise InvalidCredentialsError("password")
                return None
            try:
                return user_can_authenticate(user)
            except NotAuthenticatedError as e:
                if not is_admin:
                    raise e
                return None
        return None


class SessionAuthentication(authentication.SessionAuthentication):
    """
    An extension of :obj:`rest_framework.authentication.SessionAuthentication`
    that prevents inactive :obj:`User`(s) or :obj:`User`(s) with unverified
    email addresses from authenticating.
    """
    user_ref = 'user'
    csrf_excempt = False

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.  This is necessary to force
        DRF to return a 401 status code when authentication fails, vs. a 403
        status code.
        """
        return "Bearer"

    def authenticate(self, request):
        user = getattr(request._request, self.user_ref, None)
        if not user or not user.is_authenticated or not user.is_active \
                or not user.is_verified:
            return None
        if not self.csrf_excempt:
            self.enforce_csrf(request)
        return (user, None)


class CookieSessionAuthentication(SessionAuthentication):
    """
    An extension of :obj:`greenbudget.app.authentication.SessionAuthentication`
    that authenticates the :obj:`User` associated with the JWT token.
    """
    user_ref = 'cookie_user'


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
    csrf_excempt = True
