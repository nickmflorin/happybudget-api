from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from greenbudget.app.budget.mixins import BudgetNestedMixin
from .models import Account


class AccountNestedMixin(object):
    """
    A mixin for views that extend off of an account's detail endpoint.
    """
    @property
    def account_lookup_field(self):
        raise NotImplementedError()

    @cached_property
    def account(self):
        params = {
            self.account_lookup_field[0]: (
                self.kwargs[self.account_lookup_field[1]])
        }
        return get_object_or_404(
            Account.objects.filter(budget__trash=False), **params)


class BudgetAccountNestedMixin(BudgetNestedMixin):
    """
    A mixin for views that extend off of an account's detail endpoint that
    is extended off of a budget's detail endpoint.
    """
    @property
    def account_lookup_field(self):
        raise NotImplementedError()

    @cached_property
    def account(self):
        params = {
            self.account_lookup_field[0]: (
                self.kwargs[self.account_lookup_field[1]])
        }
        return get_object_or_404(self.budget.accounts.all(), **params)
