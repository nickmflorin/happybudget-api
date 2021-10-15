from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions

from greenbudget.lib.drf.exceptions import InvalidFieldError


class AuthErrorCodes(object):
    ACCOUNT_DISABLED = "account_disabled"
    INVALID_CREDENTIALS = "invalid_credentials"
    EMAIL_DOES_NOT_EXIST = "email_does_not_exist"
    EMAIL_NOT_VERIFIED = "email_not_verified"
    INVALID_SOCIAL_TOKEN = "invalid_social_token"
    INVALID_SOCIAL_PROVIDER = "invalid_social_provider"


class PermissionDenied(exceptions.PermissionDenied):
    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        force_logout = kwargs.pop('force_logout', None)
        if force_logout is True:
            setattr(self, 'force_logout', True)
        if user_id is not None:
            setattr(self, 'user_id', user_id)
        exceptions.PermissionDenied.__init__(self, *args, **kwargs)


class AccountDisabledError(PermissionDenied):
    default_detail = _(
        "Your account is not active, please contact customer care.")
    default_code = AuthErrorCodes.ACCOUNT_DISABLED


class EmailDoesNotExist(InvalidFieldError):
    default_detail = _(
        "The provided username does not exist in our system.")
    default_code = AuthErrorCodes.EMAIL_DOES_NOT_EXIST


class EmailNotVerified(PermissionDenied):
    default_detail = _("The email address is not verified.")
    default_code = AuthErrorCodes.EMAIL_NOT_VERIFIED


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
