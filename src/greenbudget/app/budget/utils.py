import logging

from io import BytesIO
from django.template.loader import get_template

from xhtml2pdf import pisa

from .exceptions import BudgetPdfError


logger = logging.getLogger('greenbudget')


def render_budget_as_pdf(budget):
    template = get_template('export.html')
    html = template.render({'budget': budget})
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if pdf.err:
        logger.error(pdf.err)
        raise BudgetPdfError()
    return result
