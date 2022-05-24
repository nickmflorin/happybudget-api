from django.utils.translation import gettext_lazy as _
from happybudget.app import exceptions


class PlaidRequestError(exceptions.BadRequest):
    default_code = "plaid_request_error"
    default_detail = _("There was an error communicating with Plaid.")
