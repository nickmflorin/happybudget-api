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

    @property
    def subaccount_polymorphic_instance(self):
        return None

    @cached_property
    def subaccount(self):
        params = {
            self.subaccount_lookup_field[0]: (
                self.kwargs[self.subaccount_lookup_field[1]])
        }
        qs = SubAccount.objects.filter(budget__trash=False)
        if self.subaccount_polymorphic_instance is not None:
            qs = qs.instance_of(self.subaccount_polymorphic_instance)
        return get_object_or_404(qs, **params)
