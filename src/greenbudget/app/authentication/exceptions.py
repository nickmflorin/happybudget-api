"""
django-rest-framework-simplejwt does not distinguish between tokens that are
expired but otherwise valid, and tokens that are invalid for other reasons.
We use these exceptions to distinguish these cases in our own JWT serializers
and views
"""
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions

from rest_framework_simplejwt.exceptions import (
    TokenError as BaseTokenError, InvalidToken as BaseInvalidToken)

from greenbudget.lib.drf.exceptions import InvalidFieldError


class AuthErrorCodes(object):
    ACCOUNT_DISABLED = "account_disabled"
    ACCOUNT_NOT_APPROVED = "account_not_approved"
    ACCOUNT_NOT_AUTHENTICATED = "account_not_authenticated"
    ACCOUNT_NOT_VERIFIED = "account_not_verified"
    ACCOUNT_NOT_ON_WAITLIST = "account_not_on_waitlist"
    ACCOUNT_VERIFIED = "account_verified"
    INVALID_CREDENTIALS = "invalid_credentials"
    EMAIL_DOES_NOT_EXIST = "email_does_not_exist"
    INVALID_SOCIAL_TOKEN = "invalid_social_token"
    INVALID_SOCIAL_PROVIDER = "invalid_social_provider"
    INVALID_TOKEN = "token_not_valid"
    EXPIRED_TOKEN = "token_expired"
    EMAIL_ERROR = "email_error"


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
    default_code = AuthErrorCodes.INVALID_TOKEN

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
    default_code = AuthErrorCodes.EXPIRED_TOKEN


class PermissionDenied(exceptions.PermissionDenied):
    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        force_logout = kwargs.pop('force_logout', None)
        if force_logout is True:
            setattr(self, 'force_logout', True)
        if user_id is not None:
            setattr(self, 'user_id', user_id)
        exceptions.PermissionDenied.__init__(self, *args, **kwargs)


class NotAuthenticatedError(PermissionDenied):
    default_detail = _("User is not authenticated.")
    default_code = AuthErrorCodes.ACCOUNT_NOT_AUTHENTICATED


class AccountDisabled(PermissionDenied):
    default_detail = _(
        "Your account is not active, please contact customer care.")
    default_code = AuthErrorCodes.ACCOUNT_DISABLED


class AccountNotVerified(PermissionDenied):
    default_detail = _("The email address is not verified.")
    default_code = AuthErrorCodes.ACCOUNT_NOT_VERIFIED


class AccountNotApproved(PermissionDenied):
    default_detail = _("The account is not approved.")
    default_code = AuthErrorCodes.ACCOUNT_NOT_APPROVED


class AccountVerified(PermissionDenied):
    default_detail = _("The email address is already verified.")
    default_code = AuthErrorCodes.ACCOUNT_VERIFIED


class AccountNotOnWaitlist(PermissionDenied):
    default_detail = _("The email address is not on the waitlist.")
    default_code = AuthErrorCodes.ACCOUNT_NOT_ON_WAITLIST


class EmailDoesNotExist(InvalidFieldError):
    default_detail = _(
        "The provided username does not exist in our system.")
    default_code = AuthErrorCodes.EMAIL_DOES_NOT_EXIST


class InvalidCredentialsError(InvalidFieldError):
    default_detail = _("The provided password is invalid.")
    default_code = AuthErrorCodes.INVALID_CREDENTIALS


class RateLimitedError(exceptions.Throttled):
    default_detail = _("Request limit exceeded.")
    default_code = "rate_limited"


class InvalidSocialToken(exceptions.AuthenticationFailed):
    default_detail = _(
        "The provided social token is missing or invalid.")
    default_code = AuthErrorCodes.INVALID_SOCIAL_TOKEN


class InvalidSocialProvider(exceptions.AuthenticationFailed):
    default_detail = _(
        "The provided social provider is missing or invalid.")
    default_code = AuthErrorCodes.INVALID_SOCIAL_PROVIDER


class EmailError(exceptions.ParseError):
    default_detail = _("There was a problem sending the email.")
    default_code = AuthErrorCodes.EMAIL_ERROR
