"""
django-rest-framework-simplejwt does not distinguish between tokens that are
expired but otherwise valid, and tokens that are invalid for other reasons.
We use these exceptions to distinguish these cases in our own JWT serializers
and views
"""
from django.utils.translation import ugettext_lazy as _

from rest_framework_simplejwt.exceptions import (
    TokenError as BaseTokenError, InvalidToken as BaseInvalidToken)

from greenbudget.app.authentication.exceptions import PermissionDenied


__all__ = (
    'TokenError', 'TokenInvalidError', 'TokenExpiredError', 'ExpiredToken',
    'InvalidToken')


class TokenError(BaseTokenError):
    def __init__(self, user_id=None):
        if user_id is not None:
            setattr(self, 'user_id', user_id)
        super().__init__()


class TokenInvalidError(TokenError):
    """
    An exception used by serializers when a token is invalid for reasons
    other than expiry.
    """
    pass


class TokenCorruptedError(TokenError):
    """
    An exception used by serializers when a token is invalid because it is
    associated with an invalid user ID.
    """
    pass


class TokenExpiredError(TokenError):
    """
    An exception used by serializers when a token is expired.
    """


class InvalidToken(BaseInvalidToken):
    """
    A DRF AuthenticationFailed exception used by views when a token is provided
    in the request but is invalid.
    """
    default_detail = _('Token is invalid.')
    default_code = 'token_not_valid'

    def __init__(self, detail=None, **kwargs):
        if detail == _('Token is invalid.'):
            detail = self.default_detail
        # DRF simplejwt does a weird thing with its exceptions, which messes up
        # our error formatting. By calling PermissionDenied.__init__
        # directly, we skip their strange details transformation
        PermissionDenied.__init__(self, detail=detail, **kwargs)


class ExpiredToken(InvalidToken):
    """
    A DRF AuthenticationFailed exception used by views when a token is
    expired.
    """
    default_detail = _('The provided token is expired.')
    default_code = 'token_expired'
