from collections import OrderedDict
import functools

from django.db.models import QuerySet
from rest_framework import pagination, response


def paginate_action(serializer_cls=None):
    """
    Decorator for `rest_framework.decorators.action` endpoints that allows the
    view's pagination to be applied to the queryset returned by the action
    endpoint.

    The decorated method must either return a queryset, a list of instances
    or a tuple of a queryset/list of instances and the serializer class to
    be used.

    Example:
    -------
    In the below example, we return a filtered queryset from the `custom_action`
    action and decorate the method with `paginate_action` so that the queryset
    will be paginated based on the pagination scheme for `CustomViewSet`.

    class CustomViewSet(...):

        @decorators.action(detail=False, methods=["GET"])
        @paginate_action
        def custom_action(self, request, *args, **kwargs):
            qs = self.get_queryset()
            qs = qs.filter(...)
            return qs
    """
    def decorator(func):
        @functools.wraps(func)
        def inner(instance, *args, **kwargs):
            qs = func(instance, *args, **kwargs)

            serializer_klass = serializer_cls
            if serializer_klass is None:
                serializer_klass = instance.get_serializer

            assert isinstance(
                qs, (list, QuerySet)), (
                    "The `paginate_action` decorator must decorate a method "
                    "that returns a queryset or a list.")

            page = instance.paginate_queryset(qs)
            if page is not None:
                serializer = serializer_klass(page, many=True)
                return instance.get_paginated_response(serializer.data)

            serializer = serializer_klass(qs, many=True)
            return response.Response(serializer.data)
        return inner
    return decorator


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
