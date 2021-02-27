from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied


class AuthErrorCodes(object):
    ACCOUNT_DISABLED = "account_disabled"
    INVALID_CREDENTIALS = "invalid_credentials"
    EMAIL_DOES_NOT_EXIST = "email_does_not_exist"


class AccountDisabledError(PermissionDenied):
    default_detail = _(
        "Your account is not active, please contact customer care.")
    default_code = AuthErrorCodes.ACCOUNT_DISABLED


class EmailDoesNotExist(AuthenticationFailed):
    default_detail = _(
        "The provided username does not exist in our system.")
    default_code = AuthErrorCodes.EMAIL_DOES_NOT_EXIST


class InvalidCredentialsError(AuthenticationFailed):
    default_detail = _("The provided password is invalid.")
    default_code = AuthErrorCodes.INVALID_CREDENTIALS
