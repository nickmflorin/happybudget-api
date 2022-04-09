import copy

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from greenbudget.lib.utils import cumulative_sum

from greenbudget.app import model
from greenbudget.app.budgeting.decorators import children_method_handler
from greenbudget.app.budgeting.models import (
    BudgetingTreePolymorphicOrderedRowModel)
from greenbudget.app.budgeting.utils import AssociatedModel
from greenbudget.app.group.models import Group
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.utils import contribution_from_markups
from greenbudget.app.subaccount.models import SubAccount

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


class Account(BudgetingTreePolymorphicOrderedRowModel):
    parent = models.ForeignKey(
        to='budget.BaseBudget',
        on_delete=models.CASCADE,
        related_name='children'
    )
    is_deleting = models.BooleanField(default=False)

    ESTIMATED_FIELDS = ESTIMATED_FIELDS
    CALCULATED_FIELDS = CALCULATED_FIELDS
    VALID_PARENTS = ['budget_cls']

    groups = GenericRelation(Group)
    children = GenericRelation(SubAccount)
    children_markups = GenericRelation(Markup)

    objects = AccountManager()
    non_polymorphic = models.Manager()

    table_pivot = ('parent_id', )
    child_instance_cls = AssociatedModel('subaccount_cls')

    class Meta:
        get_latest_by = "order"
        ordering = ('order', )
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        unique_together = (('parent', 'order'))

    @classmethod
    def parse_related_model_table_key_data(cls, parent):
        return {'parent_id': parent.pk}

    @property
    def nominal_value(self):
        return self.accumulated_value

    @property
    def realized_value(self):
        return self.nominal_value + self.accumulated_fringe_contribution \
            + self.accumulated_markup_contribution

    @children_method_handler
    def accumulate_value(self, children):
        previous_value = self.accumulated_value
        self.accumulated_value = cumulative_sum(children, attr='nominal_value')
        return previous_value != self.accumulated_value

    @children_method_handler
    def accumulate_markup_contribution(self, children, to_be_deleted=None):
        markups = self.children_markups.filter(unit=Markup.UNITS.flat).exclude(
            pk__in=to_be_deleted or []
        )
        previous_value = self.accumulate_markup_contribution
        self.accumulated_markup_contribution = cumulative_sum(
            children,
            attr=['markup_contribution', 'accumulated_markup_contribution']
        ) + cumulative_sum(markups, attr='rate', ignore_values=[None])
        return self.accumulated_markup_contribution != previous_value

    @children_method_handler
    def accumulate_fringe_contribution(self, children):
        previous_value = self.accumulated_fringe_contribution
        self.accumulated_fringe_contribution = cumulative_sum(
            children,
            attr=['fringe_contribution', 'accumulated_fringe_contribution']
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

    @children_method_handler
    def estimate(self, children, **kwargs):
        markups_to_be_deleted = kwargs.get('markups_to_be_deleted', []) or []
        alterations = [
            self.accumulate_value(children),
            self.accumulate_fringe_contribution(children),
            self.accumulate_markup_contribution(
                children,
                to_be_deleted=markups_to_be_deleted
            ),
            self.establish_markup_contribution(
                to_be_deleted=markups_to_be_deleted
            )
        ]
        if any(alterations):
            unsaved_recursive_children = [self]
            if kwargs.get('commit', False):
                unsaved_recursive_children = None
                self.save()
            if kwargs.get('trickle', True):
                self.parent.estimate(
                    unsaved_children=unsaved_recursive_children,
                    **kwargs
                )
        return any(alterations)

    def calculate(self, *args, **kwargs):
        return self.estimate(*args, **kwargs)


@model.model(type="account")
class BudgetAccount(Account):
    objects = BudgetAccountManager()

    pdf_type = "pdf-account"
    domain = "budget"

    class Meta(Account.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    @children_method_handler
    def actualize(self, children, **kwargs):
        markups_to_be_deleted = kwargs.get('markups_to_be_deleted', []) or []

        previous_value = self.actual
        self.actual = cumulative_sum(
            self.children_markups.exclude(pk__in=markups_to_be_deleted),
            attr='actual',
        ) + cumulative_sum(children, attr='actual')

        if self.actual != previous_value:
            unsaved = [self]
            if kwargs.get('commit', False):
                unsaved = None
                self.save(update_fields=['actual'])
            if kwargs.get('trickle', True):
                self.parent.actualize(unsaved_children=unsaved, **kwargs)
        return self.actual != previous_value

    @children_method_handler
    def calculate(self, children, **kwargs):
        alteration_kwargs = copy.deepcopy(kwargs)
        alteration_kwargs.update(trickle=False, commit=False)
        alterations = [
            super().calculate(children, **alteration_kwargs),
            self.actualize(children, **alteration_kwargs)
        ]
        if any(alterations):
            unsaved = [self]
            if kwargs.get('commit', False):
                unsaved = None
                self.save()
            if kwargs.get('trickle', True):
                self.parent.calculate(unsaved_children=unsaved, **kwargs)
        return any(alterations)


@model.model(type="account")
class TemplateAccount(Account):
    objects = TemplateAccountManager()
    domain = "template"

    class Meta(Account.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
