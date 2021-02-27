from rest_framework import authentication


class JWTCookieAuthentication(authentication.BaseAuthentication):
    """
    An extension of `rest_framework.authentication.BaseAuthentication` that
    enforces that the JWT token is valid by using the token to determine the
    currently logged in user.
    """

    def authenticate(self, request):
        user = getattr(request._request, 'cookie_user', None)
        if not user or not user.is_active:
            return None
        else:
            return (user, None)


class CsrfExcemptSessionAuthentication(authentication.SessionAuthentication):
    """
    An extension of `rest_framework.authentication.SessionAuthentication` that
    does not enforce CSRF checks.  This is required for the views to validate
    and refresh a JWT token.

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
        user = getattr(request._request, 'user', None)
        if not user or not user.is_active:
            return None
        # This is where DRF's `authentication.SessionAuthentication` would
        # enforce the CSRF check.
        return (user, None)
