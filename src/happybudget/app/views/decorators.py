import functools

from django.http import Http404
from rest_framework import decorators

from happybudget.lib.utils.urls import parse_ids_from_request


def filter_by_ids(cls):
    """
    A decorator for extensions of :obj:`rest_framework.views.ViewSet` that
    will filter the queryset by a list of IDs provided as query params in
    the URL.  Applicable for list related endpoints:
    >>> GET /budgets/<id>/accounts?ids=[1, 2, 3]
    """
    original_get_queryset = cls.get_queryset

    @property
    def request_ids(instance):
        return parse_ids_from_request(instance.request)

    def get_queryset(instance, *args, **kwargs):
        qs = original_get_queryset(instance, *args, **kwargs)
        if instance.request_ids is not None:
            qs = qs.filter(pk__in=instance.request_ids)
        return qs

    cls.request_ids = request_ids
    if original_get_queryset is not None:
        cls.get_queryset = get_queryset
    return cls


def action(**kwargs):
    """
    Overrides the default :obj:`rest_framework.decorators.action` decorator
    such that actions on a view can be hidden.
    """
    _hidden = kwargs.pop('hidden', None)

    def _decorator(func):
        @decorators.action(**kwargs)
        @functools.wraps(func)
        def inner(*args, **kwargs):
            # pylint: disable=import-outside-toplevel
            from django.conf import settings

            hidden = _hidden
            if hidden is not None and hasattr(hidden, '__call__'):
                hidden = hidden(settings)
            if hidden:
                raise Http404()
            return func(*args, **kwargs)
        return inner
    return _decorator
