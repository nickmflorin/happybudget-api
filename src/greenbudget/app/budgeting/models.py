import functools
from polymorphic.models import PolymorphicModel

from django.db import models, IntegrityError
from django.utils.functional import cached_property

from greenbudget.lib.utils import ensure_iterable, empty, humanize_list
from greenbudget.lib.django_utils.models import (
    import_model_at_path, get_value_from_model_map)

from greenbudget.app.tabling.models import (
    RowModel, OrderedRowModel, OrderedRowPolymorphicModel)


class BudgetTree:
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
    def instance_map(self):
        return {
            'budget.BaseBudget': self._budgets,
            'account.Account': self._accounts,
            'subaccount.SubAccount': self._subaccounts
        }

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
                store = get_value_from_model_map(
                    self.instance_map, instance, strict=True)
                store.add(instance)


def children_method_handler(func):
    @functools.wraps(func)
    def inner(instance, *args, **kwargs):
        children_to_delete = kwargs.pop('children_to_delete', []) or []
        unsaved_children = kwargs.pop('unsaved_children', []) or []

        # We have to be careful with empty lists here, because an empty list
        # means there are no children - so we cannot simply check `if children`.
        children = kwargs.pop('children', empty)
        if children is empty:
            if args:
                children = args[0]
            else:
                children = instance.children.all()

        assert all([
            pk in [c.pk for c in children] for pk in children_to_delete]), \
            "The children to delete must be provided as IDs of children that " \
            "exist in the instance's children or provided children."

        # If the estimation is being performed in the context of children
        # that are not yet saved (due to bulk write behavior) then we need to
        # make sure to reference the value from that unsaved child, not the
        # child that is pulled from the database.
        if isinstance(children, models.QuerySet):
            children = list(children.exclude(
                # Unsaved does not mean never saved, the child could have a PK.
                pk__in=[c.pk for c in unsaved_children if c.pk is not None]
            ))
        else:
            children = [c for c in children if c.pk not in [
                c.pk for c in unsaved_children if c.pk is not None]]
        children += ensure_iterable(unsaved_children)
        return func(
            instance,
            [c for c in children if c.pk not in children_to_delete],
            **kwargs
        )
    return inner


class AssociatedModel:
    def __init__(self, *model_lookup):
        self._model_lookup = tuple(model_lookup)

    def __get__(self, obj, objtype=None):
        if self._model_lookup == ('self', ):
            return objtype
        elif len(self._model_lookup) == 1:
            return getattr(obj, self._model_lookup[0])
        return import_model_at_path(*self._model_lookup)


class BudgetingModelMixin:
    budget_cls = AssociatedModel('budget', 'basebudget')
    account_cls = AssociatedModel('account', 'account')
    subaccount_cls = AssociatedModel('subaccount', 'subaccount')
    domain = None


class BudgetingTreeModelMixin(BudgetingModelMixin):
    @property
    def ancestors(self):
        # If the parent is a Budget or Template, it will not have any ancestors.
        if hasattr(self.parent, 'ancestors'):
            return self.parent.ancestors + [self.parent]
        return [self.parent]

    @property
    def parent_instance_cls(self):
        return type(self.parent)

    @property
    def parent_type(self):
        return self.parent.type

    @property
    def budget(self):
        parent = self.parent
        while hasattr(parent, 'parent'):
            parent = parent.parent
        return parent


class BudgetingModel(models.Model, BudgetingModelMixin):
    class Meta:
        abstract = True


class BudgetingRowModel(RowModel, BudgetingModelMixin):
    class Meta:
        abstract = True


class BudgetingOrderedRowModel(OrderedRowModel, BudgetingModelMixin):
    class Meta:
        abstract = True


class BudgetingTreePolymorphicModel(PolymorphicModel, BudgetingTreeModelMixin):
    class Meta:
        abstract = True


class BudgetingTreePolymorphicOrderedRowModel(
        OrderedRowPolymorphicModel, BudgetingTreeModelMixin):
    identifier = models.CharField(null=True, max_length=128, blank=True)
    description = models.CharField(null=True, max_length=128, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.identifier or self.description or "----"

    @property
    def valid_parent_cls(self):
        return tuple([getattr(self, attr) for attr in self.VALID_PARENTS])

    def validate_before_save(self):
        super().validate_before_save()
        # The Group that the model belongs to must have the same parent as
        # the model itself.
        if self.group is not None and self.group.parent != self.parent:
            raise IntegrityError(
                "Can only add groups with the same parent as the instance."
            )
        # The `limit_choices_to` property of the content_type ForeignKey field
        # (in the case of a GFK parent) or the the parent ForeignKey field does
        # not actually perform validation before a save, just validation via the
        # Django Admin.  We want to ensure that the parent of the model is
        # valid - even though we will get an error somewhere else if it is not,
        # it is better to perform the validation early here.
        humanized_parents = humanize_list(
            self.valid_parent_cls, conjunction="or")
        # If the parent is None, we will get an IntegrityError when saving
        # regardless, so we do not need to raise one here.
        if self.parent is not None \
                and not isinstance(self.parent, self.valid_parent_cls):
            raise IntegrityError(
                f"Type {type(self.parent)} is not a valid parent for "
                f"{self.__class__.__name__}.  Must be one of "
                f"{humanized_parents}."
            )
