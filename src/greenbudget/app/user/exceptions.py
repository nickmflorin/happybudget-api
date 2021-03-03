from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions


class UserErrorCodes(object):
    INVALID_SOCIAL_TOKEN = "invalid_social_token"
    INVALID_SOCIAL_PROVIDER = "invalid_social_provider"


class InvalidSocialToken(exceptions.ParseError):
    default_detail = _(
        "The provided social token is missing or invalid.")
    default_code = UserErrorCodes.INVALID_SOCIAL_TOKEN


class InvalidSocialProvider(exceptions.ParseError):
    default_detail = _(
        "The provided social provider is missing or invalid.")
    default_code = UserErrorCodes.INVALID_SOCIAL_PROVIDER
