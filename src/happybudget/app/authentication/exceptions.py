from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated

from rest_framework_simplejwt.exceptions import TokenError as BaseTokenError

from happybudget.app import exceptions


class NotAuthenticatedErrorCodes:
    ACCOUNT_DISABLED = "account_disabled"
    ACCOUNT_NOT_AUTHENTICATED = "account_not_authenticated"
    ACCOUNT_NOT_VERIFIED = "account_not_verified"
    ACCOUNT_NOT_ON_WAITLIST = "account_not_on_waitlist"
    INVALID_TOKEN = "token_not_valid"
    EXPIRED_TOKEN = "token_expired"


class TokenError(BaseTokenError):
    def __init__(self, user_id=None):
        if user_id is not None:
            setattr(self, 'user_id', user_id)
        super().__init__()


class NotAuthenticatedError(NotAuthenticated):
    default_detail = _("User is not authenticated.")
    default_code = NotAuthenticatedErrorCodes.ACCOUNT_NOT_AUTHENTICATED
    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        if user_id is not None:
            setattr(self, 'user_id', user_id)
        NotAuthenticated.__init__(self, *args, **kwargs)


class InvalidToken(NotAuthenticatedError):
    """
    A DRF NotAuthenticatedError exception used by views when a token is provided
    in the request but is invalid.
    """
    default_detail = _('Token is invalid.')
    default_code = NotAuthenticatedErrorCodes.INVALID_TOKEN
    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, detail=None, **kwargs):
        if detail == _('Token is invalid.'):
            detail = self.default_detail
        # DRF simplejwt does a weird thing with its exceptions, which messes up
        # our error formatting. By calling NotAuthenticated.__init__
        # directly, we skip their strange details transformation
        NotAuthenticatedError.__init__(self, detail=detail, **kwargs)


class ExpiredToken(InvalidToken):
    """
    A DRF NotAuthenticatedError exception used by views when a token is
    expired.
    """
    default_detail = _('Token is expired.')
    default_code = NotAuthenticatedErrorCodes.EXPIRED_TOKEN


class AccountDisabled(NotAuthenticatedError):
    default_detail = _("The account is not active.")
    default_code = NotAuthenticatedErrorCodes.ACCOUNT_DISABLED


class AccountNotVerified(NotAuthenticatedError):
    default_detail = _("The email address is not verified.")
    default_code = NotAuthenticatedErrorCodes.ACCOUNT_NOT_VERIFIED


class AccountNotOnWaitlist(NotAuthenticatedError):
    default_detail = _("The email address is not on the waitlist.")
    default_code = NotAuthenticatedErrorCodes.ACCOUNT_NOT_ON_WAITLIST


class AuthErrorCodes:
    INVALID_CREDENTIALS = "invalid_credentials"
    EMAIL_DOES_NOT_EXIST = "email_does_not_exist"
    INVALID_SOCIAL_TOKEN = "invalid_social_token"
    INVALID_SOCIAL_PROVIDER = "invalid_social_provider"


class EmailDoesNotExist(exceptions.InvalidFieldError):
    default_detail = _(
        "The provided username does not exist in our system.")
    default_code = AuthErrorCodes.EMAIL_DOES_NOT_EXIST


class InvalidCredentialsError(exceptions.InvalidFieldError):
    default_detail = _("The provided password is invalid.")
    default_code = AuthErrorCodes.INVALID_CREDENTIALS


class InvalidSocialToken(exceptions.AuthenticationFailed):
    default_detail = _(
        "The provided social token is missing or invalid.")
    default_code = AuthErrorCodes.INVALID_SOCIAL_TOKEN


class InvalidSocialProvider(exceptions.AuthenticationFailed):
    default_detail = _(
        "The provided social provider is missing or invalid.")
    default_code = AuthErrorCodes.INVALID_SOCIAL_PROVIDER
