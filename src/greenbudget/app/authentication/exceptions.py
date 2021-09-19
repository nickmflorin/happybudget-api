from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import (
    AuthenticationFailed, PermissionDenied, Throttled)


class AuthErrorCodes(object):
    ACCOUNT_DISABLED = "account_disabled"
    INVALID_CREDENTIALS = "invalid_credentials"
    EMAIL_DOES_NOT_EXIST = "email_does_not_exist"
    PASSWORD_RESET_LINK_EXPIRED = "password_reset_link_expired"
    PASSWORD_RESET_LINK_USED = "password_reset_link_used"
    INVALID_RESET_TOKEN = "invalid_reset_token"


class AccountDisabledError(PermissionDenied):
    default_detail = _(
        "Your account is not active, please contact customer care.")
    default_code = AuthErrorCodes.ACCOUNT_DISABLED


class PasswordResetLinkExpiredError(PermissionDenied):
    default_code = AuthErrorCodes.PASSWORD_RESET_LINK_EXPIRED
    default_detail = _("The password reset link has expired.")


class PasswordResetLinkUsedError(PermissionDenied):
    default_code = AuthErrorCodes.PASSWORD_RESET_LINK_USED
    default_detail = _("The password reset link has already been used.")


class EmailDoesNotExist(AuthenticationFailed):
    default_detail = _(
        "The provided username does not exist in our system.")
    default_code = AuthErrorCodes.EMAIL_DOES_NOT_EXIST


class InvalidCredentialsError(AuthenticationFailed):
    default_detail = _("The provided password is invalid.")
    default_code = AuthErrorCodes.INVALID_CREDENTIALS


class InvalidResetToken(PermissionDenied):
    default_detail = _("The provided token is invalid.")
    default_code = AuthErrorCodes.INVALID_RESET_TOKEN


class RateLimitedError(Throttled):
    default_detail = _("Request limit exceeded.")
    default_code = "rate_limited"
