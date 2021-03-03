from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions


class BudgetErrorCodes(object):
    NO_USER_ACCESS = "no_user_access"


class BudgetPermissionError(exceptions.PermissionDenied):
    default_detail = _(
        "The user does not have access to this budget.")
    default_code = BudgetErrorCodes.NO_USER_ACCESS
