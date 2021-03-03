from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from .models import Budget


class BudgetNestedMixin(object):
    """
    A mixin for views that extend off of a budget's detail endpoint.
    """
    @property
    def budget_lookup_field(self):
        raise NotImplementedError()

    @cached_property
    def budget(self):
        params = {
            self.budget_lookup_field[0]: (
                self.kwargs[self.budget_lookup_field[1]])
        }
        obj = get_object_or_404(Budget.objects.active(), **params)
        obj.raise_no_access(self.request.user)
        return obj
