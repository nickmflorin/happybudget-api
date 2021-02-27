"""
django-rest-framework-simplejwt does not distinguish between tokens that are
expired but otherwise valid, and tokens that are invalid for other reasons.
We use these exceptions to distinguish these cases in our own JWT serializers
and views
"""
from django.utils.translation import ugettext_lazy as _

from rest_framework import exceptions
from rest_framework_simplejwt.exceptions import (
    TokenError, InvalidToken as BaseInvalidToken)


__all__ = (
    'TokenError', 'TokenInvalidError', 'TokenExpiredError', 'ExpiredToken',
    'InvalidToken')


class TokenInvalidError(TokenError):
    """
    An exception used by serializers when a token is invalid for reasons
    other than expiry.
    """
    pass


class TokenExpiredError(TokenError):
    """
    An exception used by serializers when a token is expired.
    """
    pass


class InvalidToken(BaseInvalidToken):
    """
    A DRF AuthenticationFailed exception used by views when a token is provided
    in the request but is invalid.
    """
    default_detail = _('Token is invalid.')
    default_code = 'token_not_valid'

    def __init__(self, detail=None, code=None):
        if detail == _('Token is invalid.'):
            detail = self.default_detail
        # DRF simplejwt does a weird thing with its exceptions, which messes up
        # our error formatting. By calling AuthenticationFailed.__init__
        # directly, we skip their strange details transformation
        exceptions.AuthenticationFailed.__init__(self, detail=detail, code=code)


class ExpiredToken(InvalidToken):
    """
    A DRF AuthenticationFailed exception used by views when a token is
    expired.
    """
    default_detail = _('The provided token is expired.')
    default_code = 'token_expired'
