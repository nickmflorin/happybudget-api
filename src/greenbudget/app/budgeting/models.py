from polymorphic.models import PolymorphicModel

from django.db import models, IntegrityError

from greenbudget.lib.utils import humanize_list
from greenbudget.app.tabling.models import (
    RowModel, OrderedRowModel, OrderedRowPolymorphicModel)

from .utils import AssociatedModel, entity_text


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
        related_name='%(class)ss',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return entity_text(self)

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
