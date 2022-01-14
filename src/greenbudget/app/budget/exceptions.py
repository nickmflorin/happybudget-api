from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions


class BudgetErrorCodes(object):
    PDF_ERROR = "pdf_error"


class BudgetPdfError(exceptions.ParseError):
    default_detail = _("There was an error processing the budget PDF.")
    default_code = BudgetErrorCodes.PDF_ERROR
