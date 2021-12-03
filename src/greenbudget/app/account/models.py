import functools

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, IntegrityError

from greenbudget.app import signals
from greenbudget.app.budgeting.models import (
    BudgetingTreePolymorphicRowModel, AssociatedModel)
from greenbudget.app.group.models import Group
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.utils import contribution_from_markups
from greenbudget.app.subaccount.models import SubAccount

from .cache import (
    account_instance_cache,
    account_markups_cache,
    account_groups_cache,
    account_subaccounts_cache
)
from .managers import (
    AccountManager,
    BudgetAccountManager,
    TemplateAccountManager
)


ESTIMATED_FIELDS = (
    'accumulated_value',
    'markup_contribution',
    'accumulated_markup_contribution',
    'accumulated_fringe_contribution'
)
CALCULATED_FIELDS = ESTIMATED_FIELDS + ('actual', )


class Account(BudgetingTreePolymorphicRowModel):
    identifier = models.CharField(null=True, max_length=128)
    description = models.CharField(null=True, max_length=128)
    parent = models.ForeignKey(
        to='budget.BaseBudget',
        on_delete=models.CASCADE,
        related_name='children'
    )

    ESTIMATED_FIELDS = ESTIMATED_FIELDS
    CALCULATED_FIELDS = CALCULATED_FIELDS

    actual = models.FloatField(default=0.0)
    accumulated_value = models.FloatField(default=0.0)
    accumulated_fringe_contribution = models.FloatField(default=0.0)
    markup_contribution = models.FloatField(default=0.0)
    accumulated_markup_contribution = models.FloatField(default=0.0)

    markups = models.ManyToManyField(
        to='markup.Markup',
        related_name='accounts'
    )
    group = models.ForeignKey(
        to='group.Group',
        null=True,
        on_delete=models.SET_NULL,
        related_name='accounts'
    )
    groups = GenericRelation(Group)
    children = GenericRelation(SubAccount)
    children_markups = GenericRelation(Markup)

    objects = AccountManager()
    non_polymorphic = models.Manager()

    CACHES = [
        account_instance_cache,
        account_subaccounts_cache,
        account_markups_cache,
        account_groups_cache
    ]
    type = "account"
    table_pivot = ('parent_id', )
    child_instance_cls = AssociatedModel('subaccount_cls')

    class Meta:
        get_latest_by = "order"
        ordering = ('order', )
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        unique_together = (('parent', 'order'))

    def __str__(self):
        return "Account: %s" % self.identifier

    @property
    def ancestors(self):
        return [self.parent]

    @property
    def siblings(self):
        return self.parent.children.exclude(pk=self.pk).all()

    @property
    def budget(self):
        return self.parent

    @property
    def nominal_value(self):
        return self.accumulated_value

    @property
    def realized_value(self):
        return self.nominal_value + self.accumulated_fringe_contribution \
            + self.accumulated_markup_contribution

    def validate_before_save(self, bulk_context=False):
        if self.group is not None and self.group.parent != self.parent:
            raise IntegrityError(
                "Can only add groups with the same parent as the instance."
            )
        super().validate_before_save(bulk_context=bulk_context)

    def accumulate_value(self, children=None):
        children = children or self.children.all()
        previous_value = self.accumulated_value
        self.accumulated_value = functools.reduce(
            lambda current, sub: current + sub.nominal_value,
            children,
            0
        )
        return previous_value != self.accumulated_value

    def accumulate_markup_contribution(self, children=None, to_be_deleted=None):
        children = children or self.children.all()
        markups = self.children_markups.filter(unit=Markup.UNITS.flat).exclude(
            pk__in=to_be_deleted or []
        )

        previous_value = self.accumulate_markup_contribution
        self.accumulated_markup_contribution = functools.reduce(
            lambda current, sub: current + sub.markup_contribution
            + sub.accumulated_markup_contribution,
            children,
            0
        ) + functools.reduce(
            lambda current, markup: current + (markup.rate or 0.0),
            markups,
            0
        )
        return self.accumulated_markup_contribution != previous_value

    def accumulate_fringe_contribution(self, children=None):
        children = children or self.children.all()
        previous_value = self.accumulated_fringe_contribution
        self.accumulated_fringe_contribution = functools.reduce(
            lambda current, sub: current + sub.fringe_contribution
            + sub.accumulated_fringe_contribution,
            children,
            0
        )
        return previous_value != self.accumulated_fringe_contribution

    def establish_markup_contribution(self, to_be_deleted=None):
        # Markups are applied after the Fringes are applied to the value.
        previous_value = self.markup_contribution
        self.markup_contribution = contribution_from_markups(
            value=self.realized_value,
            markups=self.markups.exclude(pk__in=to_be_deleted or [])
        )
        return self.markup_contribution != previous_value

    def estimate(self, **kwargs):
        children, kwargs = self.children_from_kwargs(**kwargs)
        trickle = kwargs.pop('trickle', True)
        commit = kwargs.get('commit', False)
        markups_to_be_deleted = kwargs.get('markups_to_be_deleted', []) or []

        alterations = [
            self.accumulate_value(children=children),
            self.accumulate_fringe_contribution(children=children),
            self.accumulate_markup_contribution(
                children=children,
                to_be_deleted=markups_to_be_deleted
            ),
            self.establish_markup_contribution(
                to_be_deleted=markups_to_be_deleted
            )
        ]
        if any(alterations):
            unsaved_recursive_children = [self]
            if commit:
                unsaved_recursive_children = None
                self.save(update_fields=self.reestimated_fields)

            # There are cases with CASCADE deletes where a non-nullable field
            # will be temporarily null.
            if trickle and self.parent is not None:
                self.parent.estimate(
                    unsaved_children=unsaved_recursive_children,
                    **kwargs
                )
        return any(alterations)

    def calculate(self, **kwargs):
        return self.estimate(**kwargs)


@signals.model(user_field='updated_by')
class BudgetAccount(Account):
    objects = BudgetAccountManager()

    pdf_type = "pdf-account"
    domain = "budget"
    budget_cls = AssociatedModel('budget', 'budget')
    account_cls = AssociatedModel('account', 'budgetaccount')
    subaccount_cls = AssociatedModel('subaccount', 'budgetsubaccount')

    class Meta(Account.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    def actualize(self, **kwargs):
        children, kwargs = self.children_from_kwargs(**kwargs)
        trickle = kwargs.pop('trickle', True)
        commit = kwargs.get('commit', False)
        markups_to_be_deleted = kwargs.get('markups_to_be_deleted', []) or []

        previous_value = self.actual
        self.actual = functools.reduce(
            lambda current, markup: current + (markup.actual or 0),
            self.children_markups.exclude(pk__in=markups_to_be_deleted),
            0
        ) + functools.reduce(
            lambda current, child: current + (child.actual or 0),
            children,
            0
        )
        if self.actual != previous_value:
            unsaved_recursive_children = [self]
            if commit:
                unsaved_recursive_children = None
                self.save(update_fields=['actual'])

            # There are cases with CASCADE deletes where a non-nullable field
            # will be temporarily null.
            if trickle and self.parent is not None:
                self.parent.actualize(
                    unsaved_children=unsaved_recursive_children,
                    **kwargs
                )
        return self.actual != previous_value

    def calculate(self, **kwargs):
        children, kwargs = self.children_from_kwargs(**kwargs)
        trickle = kwargs.pop('trickle', True)
        commit = kwargs.pop('commit', False)

        alterations = [
            super().calculate(
                children=children,
                trickle=False,
                commit=False,
                **kwargs
            ),
            self.actualize(
                children=children,
                trickle=False,
                commit=False,
                **kwargs
            )
        ]
        if any(alterations):
            unsaved_recursive_children = [self]
            if commit:
                unsaved_recursive_children = None
                self.save(
                    update_fields=tuple(self.reestimated_fields) + ('actual', ))

            if trickle and self.parent is not None:
                self.parent.calculate(
                    commit=commit,
                    unsaved_children=unsaved_recursive_children,
                    **kwargs
                )
        return any(alterations)


@signals.model(user_field='updated_by')
class TemplateAccount(Account):
    objects = TemplateAccountManager()
    domain = "template"
    budget_cls = AssociatedModel('template', 'template')
    account_cls = AssociatedModel('account', 'templateaccount')
    subaccount_cls = AssociatedModel('subaccount', 'templatesubaccount')

    class Meta(Account.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
