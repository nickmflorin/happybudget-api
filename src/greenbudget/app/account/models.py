import functools

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, IntegrityError

from greenbudget.app import signals
from greenbudget.app.budgeting.models import BudgetingPolymorphicModel
from greenbudget.app.group.models import Group
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.utils import contribution_from_markups
from greenbudget.app.subaccount.models import SubAccount

from .cache import (
    account_detail_cache,
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


class Account(BudgetingPolymorphicModel):
    type = "account"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    identifier = models.CharField(null=True, max_length=128)
    description = models.CharField(null=True, max_length=128)
    parent = models.ForeignKey(
        to='budget.BaseBudget',
        on_delete=models.CASCADE,
        related_name='children'
    )

    ESTIMATED_FIELDS = ESTIMATED_FIELDS
    CALCULATED_FIELDS = CALCULATED_FIELDS
    FIELDS_TO_DUPLICATE = ('identifier', 'description') + CALCULATED_FIELDS

    actual = models.FloatField(default=0.0)
    accumulated_value = models.FloatField(default=0.0)
    accumulated_fringe_contribution = models.FloatField(default=0.0)
    markup_contribution = models.FloatField(default=0.0)
    accumulated_markup_contribution = models.FloatField(default=0.0)

    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_accounts',
        on_delete=models.CASCADE,
        editable=False,
    )
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_accounts',
        on_delete=models.CASCADE,
        editable=False,
    )
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
        account_detail_cache,
        account_subaccounts_cache,
        account_markups_cache,
        account_groups_cache
    ]

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('created_at', )
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

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

    def validate_before_save(self):
        if self.group is not None and self.group.parent != self.parent:
            raise IntegrityError(
                "Can only add groups with the same parent as the instance."
            )

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
        markups = self.children_markups.filter(unit=Markup.UNITS.flat)

        previous_value = self.accumulate_markup_contribution
        self.accumulated_markup_contribution = functools.reduce(
            lambda current, sub: current + sub.markup_contribution
            + sub.accumulated_markup_contribution,
            children,
            0
        ) + functools.reduce(
            lambda current, markup: current + (markup.rate or 0),
            markups.exclude(pk__in=to_be_deleted or []),
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
    pdf_type = "pdf-account"
    access = models.ManyToManyField(
        to='user.User',
        related_name='accessible_accounts'
    )
    objects = BudgetAccountManager()

    class Meta(Account.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    @property
    def child_instance_cls(self):
        from greenbudget.app.subaccount.models import BudgetSubAccount
        return BudgetSubAccount

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

    FIELDS_TO_DERIVE = ('identifier', 'description') + Account.CALCULATED_FIELDS

    class Meta(Account.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    @property
    def child_instance_cls(self):
        from greenbudget.app.subaccount.models import TemplateSubAccount
        return TemplateSubAccount
