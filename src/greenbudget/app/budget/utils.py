import logging
from io import BytesIO
import os
from xhtml2pdf import pisa

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.exceptions import SuspiciousFileOperation
from django.template.loader import get_template

from .exceptions import BudgetPdfError


logger = logging.getLogger('greenbudget')


def render_budget_as_pdf(budget):
    template = get_template('export.html')
    html = template.render({'budget': budget})
    result = BytesIO()

    def fetch_resources(uri, rel):
        def is_uri_configured(uri):
            return (settings.MEDIA_URL != "/"
                and uri.startswith(settings.MEDIA_URL)) \
                or (settings.STATIC_URL != "/"
                and uri.startswith(settings.STATIC_URL))

        def get_path_from_configured_uri(uri):
            if settings.MEDIA_URL != "/" and uri.startswith(settings.MEDIA_URL):
                return os.path.join(
                    settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
            else:
                assert settings.STATIC_URL != "/" \
                    and uri.startswith(settings.STATIC_URL)
                return os.path.join(
                    settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))

        def get_path_from_uri(uri):
            try:
                result = finders.find(uri)
            except SuspiciousFileOperation:
                if not is_uri_configured(uri):
                    return None
                return get_path_from_configured_uri(uri)
            else:
                if result:
                    if not isinstance(result, (list, tuple)):
                        result = [result]
                    result = list(os.path.realpath(path) for path in result)
                    return result[0]
                else:
                    if not is_uri_configured(uri):
                        return None
                    return get_path_from_configured_uri(uri)

        path = get_path_from_uri(uri)
        if path is None:
            return uri
        if not os.path.isfile(path):
            import ipdb
            ipdb.set_trace()
            raise Exception('Media URI must start with %s or %s'
                % (settings.STATIC_URL, settings.MEDIA_URL))
        print(path)
        return path

    pdf = pisa.CreatePDF(html.encode("UTF-8"), result, encoding='UTF-8',
               link_callback=fetch_resources)

    # pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if pdf.err:
        logger.error(pdf.err)
        raise BudgetPdfError()
    return result
