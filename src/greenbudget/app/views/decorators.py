from greenbudget.lib.utils.urls import parse_ids_from_request


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

