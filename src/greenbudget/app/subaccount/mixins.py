from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from .models import SubAccount


class SubAccountNestedMixin(object):
    """
    A mixin for views that extend off of an subaccount's detail endpoint.
    """
    @property
    def subaccount_lookup_field(self):
        raise NotImplementedError()

    @cached_property
    def subaccount(self):
        params = {
            self.subaccount_lookup_field[0]: (
                self.kwargs[self.subaccount_lookup_field[1]])
        }
        # TODO: How do we filter for only subaccounts whose budget is not
        # in the trash?  Because the parent can be both a budget and a
        # subaccount.
        return get_object_or_404(SubAccount.objects.all(), **params)
