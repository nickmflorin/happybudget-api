import functools
from polymorphic.models import PolymorphicModel

from django.db import models, IntegrityError
from django.utils.functional import cached_property

from greenbudget.lib.utils import (
    ensure_iterable, empty, humanize_list, get_nested_attribute)
from greenbudget.lib.django_utils.models import (
    import_model_at_path, ModelImportMap, ModelMap)

from greenbudget.app.tabling.models import (
    RowModel, OrderedRowModel, OrderedRowPolymorphicModel)


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


def children_method_handler(func):
    """
    Decorates a methods on a :obj:`BaseBudget`, :obj:`Account` or
    :obj:`SubAccount` that accept a `children` argument and perform calculations
    based on the accumulation of values of the children of the instance whose
    method this decorates.

    Exposed Parameters:
    ------------------
    The decorator will expose the following parameters on the method:

    children: :obj:`django.db.models.QuerySet` or an iterable (optional)
        The children that should be used to perform the calculation.  If
        omitted, the `children` will be determined from a database query
        of the related models on the instance that are defined to be the
        children.

        Default: None

    children_to_delete: :obj:`list`, :obj:`tuple` or another iterable (optional)
        A iterable of IDs associated with the children of the instance that are
        going to be deleted.  If provided, the children associated with these
        IDs will be excluded from the calculation.

        Default: None

    unsaved_children: :obj:`list` or :obj:`tuple` or another iterable
        An iterable of children instances that have been updated but not yet
        persisted to the database.  If provided, the children that are either
        explicitly provided or determined from a database query will be
        supplemented with the updated forms of the instances dictated by this
        parameter.

        This is important when performing bulk changes, as there are cases where
        we want to reperform calculations on models but have not yet saved
        children of the model instance that were updated to the database yet.

        Note:  Unsaved does not mean never-saved, the unsaved children should
               all have associated IDs.

        Default: None

    All of the exposed parameters are combined to a single `children` parameter
    that the method is then called with.
    """
    @functools.wraps(func)
    def inner(instance, *args, **kwargs):
        # Any potential children that are going to be deleted but have yet to
        # be deleted from the database.  These children will be exclued from
        # the children passed into the method.
        children_to_delete = kwargs.pop('children_to_delete', []) or []

        # Any potential children to the instance that have been altered but not
        # yet persisted to the database.  These instances will supplement the
        # children passed into the method such that the children passed into the
        # method contain up to date information - even if it hasn't persisted
        # to the database yet.
        unsaved_children = kwargs.pop('unsaved_children', []) or []

        # We have to be careful with empty lists here, because an empty list
        # means there are no children - so we cannot simply check `if children`.
        children = kwargs.pop('children', empty)
        if children is empty:
            if args:
                children = args[0]
            else:
                # Perform the database query to get the instance children.
                # Note that these children will not be representative of any
                # unsaved changes until they are supplemented with the
                # `unsaved_children`.
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


class BudgetingModelMixin:
    budget_cls = AssociatedModel("budget")
    account_cls = AssociatedModel("account")
    subaccount_cls = AssociatedModel("subaccount")
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
    actual = models.FloatField(default=0.0, blank=True)
    # The nominal values accumulated from all children.
    accumulated_value = models.FloatField(default=0.0)
    # The fringe contributions accumulated from all children.
    accumulated_fringe_contribution = models.FloatField(default=0.0)
    # The contribution of the markups associated with the instance to the
    # instance's estimated value.
    markup_contribution = models.FloatField(default=0.0)
    # The markup contributions accumulated from all children.
    accumulated_markup_contribution = models.FloatField(default=0.0)

    markups = models.ManyToManyField(
        to='markup.Markup',
        related_name='%(class)ss'
    )
    group = models.ForeignKey(
        to='group.Group',
        null=True,
        on_delete=models.SET_NULL,
        related_name='%(class)ss'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.identifier) or str(self.description) or "----"

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
