from django.utils.functional import cached_property

from greenbudget.lib.utils import ensure_iterable, get_nested_attribute
from greenbudget.lib.django_utils.models import (
    import_model_at_path, ModelImportMap, ModelMap)


TreeDomainModelMap = {
    None: ModelImportMap(
        budget='budget.BaseBudget',
        account='account.Account',
        subaccount='subaccount.SubAccount'
    ),
    'budget': ModelImportMap(
        budget='budget.Budget',
        account='account.BudgetAccount',
        subaccount='subaccount.BudgetSubAccount'
    ),
    'template': ModelImportMap(
        budget='template.Template',
        account='account.TemplateAccount',
        subaccount='subaccount.TemplateSubAccount'
    )
}


class BudgetTree:
    """
    Manages the related :obj:`BaseBudget`, :obj:`Account` and :obj:`SubAccount`
    instances that are related to one another with behavior that mimics that
    of a :obj:`set`.
    """
    def __init__(self, budgets=None, accounts=None, subaccounts=None):
        self._budgets = ensure_iterable(budgets, cast=set)
        self._accounts = ensure_iterable(accounts, cast=set)
        self._subaccounts = ensure_iterable(subaccounts, cast=set)

    @property
    def budgets(self):
        return self._budgets

    @property
    def accounts(self):
        return self._accounts

    @property
    def subaccounts(self):
        return self._subaccounts

    @cached_property
    def model_map(self):
        return ModelMap({
            'budget.BaseBudget': self._budgets,
            'account.Account': self._accounts,
            'subaccount.SubAccount': self._subaccounts
        })

    def merge(self, tree):
        self._budgets.update(tree.budgets)
        self._accounts.update(tree.accounts)
        self._subaccounts.update(tree.subaccounts)

    def difference(self, tree):
        self._budgets = self._budgets.difference(tree.budgets)
        self._accounts = self._accounts.difference(tree.accounts)
        self._subaccounts = self._subaccounts.difference(tree.subaccounts)

    def add(self, *args):
        for instances in args:
            for instance in ensure_iterable(instances, cast=set):
                store = self.model_map.get(instance, strict=True)
                store.add(instance)


class AssociatedModel:
    def __init__(self, *model_lookup):
        self._model_lookup = tuple(model_lookup)

    def __get__(self, obj, objtype=None):
        if self._model_lookup == ('self', ):
            return objtype
        elif len(self._model_lookup) == 1:
            if self._model_lookup[0] in ('budget', 'account', 'subaccount'):
                # The obj may be None, in which case the objtype is provided.
                obj_type = objtype or type(obj)
                assert hasattr(obj_type, 'domain'), \
                    "If the model type is provided, the domain must be " \
                    f"attributed on model {obj_type.__name__}."
                domain = getattr(obj_type, 'domain')
                return getattr(TreeDomainModelMap[domain], self._model_lookup[0])
            return get_nested_attribute(obj, self._model_lookup[0])
        return import_model_at_path(*self._model_lookup)
