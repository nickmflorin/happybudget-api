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
    page_size = 20
    page_query_param = 'page'
    page_size_query_param = 'page_size'

    def paginate_queryset(self, queryset, request, view=None):
        # Allow the pagination to be completely turned off on a per-request
        # basis.
        if 'no_pagination' in request.query_params:
            self._no_pagination = True
            return queryset
        return super().paginate_queryset(queryset, request, view)

    def get_response_data(self, data, **kwargs):
        return [
            ('count', len(data)),
            ('data', data),
        ]

    def get_paginated_response(self, data, **kwargs):
        if getattr(self, '_no_pagination', False) is True:
            return response.Response(
                OrderedDict(
                    self.get_response_data(data, **kwargs)
                    + [('next', None), ('previous', None)]
                )
            )
        return response.Response(OrderedDict(
            self.get_response_data(data, **kwargs)
            + [
                ('next', self.get_next_link()),
                ('previous', self.get_previous_link()),
            ])
        )
