import collections
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from rest_framework import authentication

from .exceptions import (
    EmailNotVerified, AccountDisabledError, EmailDoesNotExist,
    InvalidCredentialsError, NotAuthenticatedError)


logger = logging.getLogger('greenbudget')


UserPermissionValidator = collections.namedtuple(
    'UserPermissionValidator', ['id', 'check', 'exception'])

UserPermissionValidators = [
    UserPermissionValidator(
        id='authenticated',
        check=lambda user: user is None or not user.is_authenticated,
        exception=NotAuthenticatedError
    ),
    UserPermissionValidator(
        id='active',
        check=lambda user: not user.is_active,
        exception=AccountDisabledError
    ),
    UserPermissionValidator(
        id='verified',
        check=lambda user: not user.is_verified,
        exception=EmailNotVerified
    )
]


def check_user_permissions(user, force_logout=False, raise_exception=False,
        exclude_permissions=None):
    exclude = exclude_permissions or []
    for validator in [
            v for v in UserPermissionValidators if v.id not in exclude]:
        if validator.check(user) is True:
            if raise_exception:
                if user is not None and getattr(user, 'pk') is not None:
                    raise validator.exception(
                        user_id=user.pk,
                        force_logout=force_logout
                    )
                raise validator.exception(force_logout=force_logout)
            return False
    return True


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
            check_user_permissions(user, raise_exception=True)
            return user
        return None


class ModelAuthentication(ModelBackend):
    """
    An extension of :obj:`django.contrib.auth.backends.ModelBackend` that
    enforces that a user has a verified email address before allowing them
    to fully login.
    """

    def authenticate(self, request, email=None, password=None):
        if email is not None and password is not None:
            try:
                user = get_user_model().objects.get(email=email)
            except get_user_model().DoesNotExist:
                raise EmailDoesNotExist('email')

            if not user.check_password(password):
                raise InvalidCredentialsError("password")
            check_user_permissions(user, raise_exception=True)
            return user
        return None


class SessionAuthentication(authentication.SessionAuthentication):
    """
    An extension of :obj:`rest_framework.authentication.SessionAuthentication`
    that prevents :obj:`User`(s) with unverified email addresses from logging
    in.

    Additionally, when the user cannot be authenticated this authentication
    protocol will raise an extension of
    :obj:`greengudget.app.authentication.exceptions.PermissionDenied` instead
    of simply returning None.  This is done so the raised Exception can trigger
    the proper actions to forcefully log the user out.
    """
    user_ref = 'user'
    exclude_permissions = []
    csrf_excempt = False

    def get_user_from_request(self, request):
        return getattr(request._request, self.user_ref, None)

    def authenticate(self, request):
        user = self.get_user_from_request(request)
        check_user_permissions(
            user=user,
            raise_exception=True,
            exclude_permissions=self.exclude_permissions
        )
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
