from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from rest_framework import authentication

from .exceptions import InvalidCredentialsError, EmailDoesNotExist
from .utils import user_can_authenticate, request_is_admin


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
    adds the following enhancements:

    (1) Performs additional checks on the :obj:`User` instance (such as
        ensuring that their email address is verified) before allowing the
        :obj:`User` to login.

    (2) Raises exceptions that trigger our error response handling instead
        of returning None, in the case that the :obj:`User` is not successfully
        authenticated.

    In the case that the login request is coming from the Admin, we have to
    use the default behavior (returning None) because the Admin is not built
    to handle DRF exceptions.
    """

    def authenticate(self, request, username=None, email=None, password=None):
        # When logging in from the Django Admin, it will pass the value in as
        # the username.
        email = email or username
        if email is not None and password is not None:
            try:
                user = get_user_model().objects.get(email=email)
            except get_user_model().DoesNotExist:
                # If we are coming from the Admin, we do not want to raise a
                # DRF exception as it will not render in the response, it will
                # just be a 500 error.
                if not request_is_admin(request):
                    raise EmailDoesNotExist(field='email')
                return None
            if not user.check_password(password):
                # If we are coming from the Admin, we do not want to raise a
                # DRF exception as it will not render in the response, it will
                # just be a 500 error.
                if not request_is_admin(request):
                    raise InvalidCredentialsError(field="password")
                return None
            return user_can_authenticate(
                user, raise_exception=not request_is_admin(request))
        return None


class SessionAuthentication(authentication.SessionAuthentication):
    """
    An extension of :obj:`rest_framework.authentication.SessionAuthentication`
    that performs additional checks on the :obj:`User` before it treats the
    :obj:`User` as having been authenticated.  These additional checks are:

    (1) Ensures the :obj:`User` is not disabled.
    (2) Ensures the :obj:`User` has gone through the process of email
        verification.

    Furthermore, this extension allows subclasses to extend it such that
    CSRF checks are bypassed.

    Enforcing CSRF
    --------------
    Django REST Framework basically prevents the CSRFViewMiddleware from being
    used by decorating any API View with @csrf_exempt under the hood.  It then
    expliitly performs the CSRF check on it's own, inside of the `authenticate`
    method on their `rest_framework.authentication.SessionAuthentication`. This
    means that decorating our views that use session authentication (which they
    do by default) with @csrf_excempt does nothing...

    In order to allow certain views that are authenticated to bypass CSRF checks
    we have to conditionally enforce the CSRF checks in the authentication class,
    and then use that authentication class on the view.
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
        if not user_can_authenticate(user, raise_exception=False):
            return None
        # Here, instead of always enforcing CSRF checks, only do so if the
        # specific authentication class does not bypass CSRF checks.
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
    """
    csrf_excempt = True


class CsrfExcemptPublicAuthentication(CsrfExcemptCookieSessionAuthentication):
    """
    An extension of :obj:`CsrfExcemptCookieSessionAuthentication` that provides
    the authentication header `WWW-Authenticate` for public token authentication
    protocols.
    """
    user_ref = 'user'

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.  This is necessary to force
        DRF to return a 401 status code when authentication fails, vs. a 403
        status code.
        """
        return settings.PUBLIC_TOKEN_HEADER
