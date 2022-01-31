from django.db import models
from django.db.models.functions import Concat

from rest_framework import filters

from .models import Contact


class ContactSearchFilterBackend(filters.SearchFilter):
    """
    Search filter for endpoints that return a list response of :obj:`Contact`
    instances.

    The filter is designed to allow :obj:`Contact`(s) to be searched by a more
    general `name` parameter (which looks at both the first and last names) as
    well as allowing :obj:`Contact`(s) to be searched a `label` parameter, that
    searches the :obj:`Contact`(s) by the company name when the :obj:`Contact`(s)
    is of type VENDOR.
    """

    def filter_queryset(self, request, queryset, view):
        qs = queryset.annotate(
            name=models.Case(
                models.When(
                    first_name=None,
                    last_name=None,
                    then=models.Value(None)
                ),
                models.When(
                    first_name=None,
                    then=models.F('last_name')
                ),
                models.When(
                    last_name=None,
                    then=models.F('first_name')
                ),
                default=Concat(
                    models.F('first_name'),
                    models.Value(' '),
                    models.F('last_name'),
                    output_field=models.CharField()
                )
            ),
            label=models.Case(
                models.When(
                    contact_type=Contact.TYPES.vendor,
                    then=models.F('company'),
                ),
                default=None
            )
        )
        return super().filter_queryset(request, qs, view)
