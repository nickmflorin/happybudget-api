from django.db import models

from happybudget.app.user.filters import FullNameSearchFilter

from .models import Contact


class ContactSearchFilterBackend(FullNameSearchFilter):
    """
    Search filter for endpoints that return a list response of :obj:`Contact`
    instances.

    The filter implements (2) behaviors over the standard behavior of the
    :obj:`rest_framework.filters.SearchFilter` class:

    (1) Allowing instances to be searched by the more general, combined `name`
        field, which is composed of the `first_name` and `last_name` fields of
        the :obj:`User` instance.

    (2) Allowing instances to be searched by a `label` parameter, that searches
        the :obj:`Contact` instances by the `company`, instead of the
        `name`, in the case that the :obj:`Contact` is of type VENDOR.
    """
    def filter_queryset(self, request, queryset, view):
        qs = queryset.annotate_name().annotate(label=models.Case(
            models.When(
                contact_type=Contact.TYPES.vendor,
                then=models.F('company'),
            ),
            default=None
        ))
        return super().filter_queryset(request, qs, view)
