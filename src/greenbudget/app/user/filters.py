from django.db.models.constants import LOOKUP_SEP
from rest_framework import filters

from greenbudget.lib.utils.urls import parse_ids_from_request


class FullNameSearchFilter(filters.SearchFilter):
    """
    An extension of :obj:`rest_framework.filters.SearchFilter` that should be
    used when the searching a model instance that has `first_name` and
    `last_name` fields that want to be treated as a more general, combined
    `name` field.

    The queryset model instance must have `first_name` and `last_name` fields
    and the queryset class must expose a `annotate_name` method.
    """
    def get_search_terms(self, request):
        """
        Overrides the default :obj:`rest_framework.filters.SearchFilter` method
        such that white space characters are not treated like delimiters.  If
        not overridden, searching a full name would result in two distinct
        searches for each part of the name.
        """
        params = request.query_params.get(self.search_param, '')
        params = params.replace('\x00', '')
        # Here, we omit the line that replaces a comma with a white space and
        # change the split to be performed on a comma, instead of a white space.
        return params.split(',')

    def filter_queryset(self, request, queryset, view):
        assert hasattr(queryset, 'annotate_name'), \
            f"The queryset {queryset.__class__.__name__} must expose a " \
            "`annotate_name` method."
        qs = queryset.annotate_name()
        exclude_ids = parse_ids_from_request(request, param='exclude')
        if exclude_ids:
            qs = qs.exclude(pk__in=exclude_ids)
        return super().filter_queryset(request, qs, view)


class UserSearchFilterBackend(FullNameSearchFilter):
    """
    Search filter for endpoints that return a list response of :obj:`User`
    instances.

    The filter implements (2) behaviors over the standard behavior of the
    :obj:`rest_framework.filters.SearchFilter` class:

    (1) Allowing instances to be searched by the more general, combined `name`
        field, which is composed of the `first_name` and `last_name` fields of
        the :obj:`User` instance.

    (2) Enforcing that the search only yields results when the search terms
        match the fields of the instance exactly.  This is done such that
        blanket searches of the users in the application cannot be performed,
        and the user performing the search must be aware of what the attribute
        values on the :obj:`User` instance, which are associated with the search
        fields, are before performing the search.

    Note that (2) can also be enforced by prefacing the fields in the
    `search_fields` attribute on the view with "=", but doing it here more
    safely ensures that the search will always only yield results in the case
    of exact matches.
    """
    def construct_search(self, field_name):
        return LOOKUP_SEP.join([field_name, 'iexact'])
