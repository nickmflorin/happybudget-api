from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions


class AuthErrorCodes(object):
    ACCOUNT_DISABLED = "account_disabled"
    INVALID_CREDENTIALS = "invalid_credentials"
    EMAIL_DOES_NOT_EXIST = "email_does_not_exist"
    EMAIL_NOT_VERIFIED = "email_not_verified"
    PASSWORD_RESET_LINK_EXPIRED = "password_reset_link_expired"
    PASSWORD_RESET_LINK_USED = "password_reset_link_used"
    INVALID_RESET_TOKEN = "invalid_reset_token"
    INVALID_SOCIAL_TOKEN = "invalid_social_token"
    INVALID_SOCIAL_PROVIDER = "invalid_social_provider"


class AccountDisabledError(exceptions.PermissionDenied):
    default_detail = _(
        "Your account is not active, please contact customer care.")
    default_code = AuthErrorCodes.ACCOUNT_DISABLED


class PasswordResetLinkExpiredError(exceptions.PermissionDenied):
    default_code = AuthErrorCodes.PASSWORD_RESET_LINK_EXPIRED
    default_detail = _("The password reset link has expired.")


class PasswordResetLinkUsedError(exceptions.PermissionDenied):
    default_code = AuthErrorCodes.PASSWORD_RESET_LINK_USED
    default_detail = _("The password reset link has already been used.")


class EmailDoesNotExist(exceptions.AuthenticationFailed):
    default_detail = _(
        "The provided username does not exist in our system.")
    default_code = AuthErrorCodes.EMAIL_DOES_NOT_EXIST


class EmailNotVerified(exceptions.AuthenticationFailed):
    default_detail = _("The email address is not verified.")
    default_code = AuthErrorCodes.EMAIL_NOT_VERIFIED


class InvalidCredentialsError(exceptions.AuthenticationFailed):
    default_detail = _("The provided password is invalid.")
    default_code = AuthErrorCodes.INVALID_CREDENTIALS


class InvalidResetToken(exceptions.PermissionDenied):
    default_detail = _("The provided token is invalid.")
    default_code = AuthErrorCodes.INVALID_RESET_TOKEN


class RateLimitedError(exceptions.Throttled):
    default_detail = _("Request limit exceeded.")
    default_code = "rate_limited"


class InvalidSocialToken(exceptions.ParseError):
    default_detail = _(
        "The provided social token is missing or invalid.")
    default_code = AuthErrorCodes.INVALID_SOCIAL_TOKEN


class InvalidSocialProvider(exceptions.ParseError):
    default_detail = _(
        "The provided social provider is missing or invalid.")
    default_code = AuthErrorCodes.INVALID_SOCIAL_PROVIDER
