from django.utils.translation import gettext_lazy as _
from greenbudget.app import exceptions


class BudgetErrorCodes(object):
    PDF_ERROR = "pdf_error"


class BudgetPdfError(exceptions.BadRequest):
    default_detail = _("There was an error processing the budget PDF.")
    default_code = BudgetErrorCodes.PDF_ERROR
