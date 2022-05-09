from collections import OrderedDict
from rest_framework import pagination, response


class Pagination(pagination.PageNumberPagination):
    """
    Extension of `rest_framework.pagination.PageNumberPagination` that will
    always include the `count` and `data` params in the response, instead of
    only including when pagination parameters are present on the request.

    Traditionally, if you send a request without pagination parameters
    (e.g. GET /budgets), DRF will return a response body as [{...}, {...}].
    If you send a request as GET /budgets?page_size=10, DRF will return a
    response body as {'count': X, 'data': [{...}, {...}]}.

    This discrepancy is confusing for the FE, as we cannot always keep track
    of what format to expect.  For this reason, we always return the response
    body as {'count': X, 'data': [{...}, {...}]}, where `count` references
    the total number of elements in the returned response in the case that
    the `page_size` pagination parameter is not included in the request.

    By default, the paginator will not paginate results unless page and/or
    page_size are provided.
    """
    page_size = None  # Do not paginate unless pagination params are provided.
    page_query_param = 'page'
    page_size_query_param = 'page_size'

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return queryset
        return super().paginate_queryset(queryset, request, view=view)

    def get_paginated_response(self, data):
        count = len(data)
        if getattr(self, 'page', None) is not None:
            count = self.page.paginator.count

        return response.Response(OrderedDict([
            ('count', count),
            ('data', data)
        ]))
