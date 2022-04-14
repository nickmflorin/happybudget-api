from django.utils.translation import gettext_lazy as _
from greenbudget.app import exceptions


class EmailError(exceptions.BadRequest):
    default_detail = _("There was a problem sending the email.")
