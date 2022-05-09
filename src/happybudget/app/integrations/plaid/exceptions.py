from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions


class PlaidErrorCodes:
    PLAID_REQUEST_ERROR = "plaid_request_error"


class PlaidRequestError(exceptions.ParseError):
    default_code = PlaidErrorCodes.PLAID_REQUEST_ERROR
    default_detail = _("There was an error communicating with Plaid.")
