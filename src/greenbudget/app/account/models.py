import functools
from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from greenbudget.app import signals
from greenbudget.app.comment.models import Comment
from greenbudget.app.group.models import Group
from greenbudget.app.history.models import Event
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.utils import contribution_from_markups
from greenbudget.app.subaccount.models import SubAccount

from .managers import AccountManager


ESTIMATED_FIELDS = (
    'accumulated_value',
    'markup_contribution',
    'accumulated_markup_contribution',
    'accumulated_fringe_contribution'
)
CALCULATED_FIELDS = ESTIMATED_FIELDS + ('actual', )


class Account(PolymorphicModel):
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

    def accumulate_value(self, children=None):
        children = children or self.children.all()
        self.accumulated_value = functools.reduce(
            lambda current, sub: current + sub.nominal_value,
            children,
            0
        )

    def accumulate_markup_contribution(self, children=None, to_be_deleted=None):
        children = children or self.children.all()
        markups = self.children_markups.filter(unit=Markup.UNITS.flat)
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

    def accumulate_fringe_contribution(self, children=None):
        children = children or self.children.all()
        self.accumulated_fringe_contribution = functools.reduce(
            lambda current, sub: current + sub.fringe_contribution
            + sub.accumulated_fringe_contribution,
            children,
            0
        )

    def establish_markup_contribution(self, to_be_deleted=None):
        # Markups are applied after the Fringes are applied to the value.
        self.markup_contribution = contribution_from_markups(
            value=self.realized_value,
            markups=self.markups.exclude(pk__in=to_be_deleted or [])
        )

    def actualize(self, children=None, markups_to_be_deleted=None):
        children = children or self.children.all()
        self.actual = functools.reduce(
            lambda current, markup: current + (markup.actual or 0),
            self.children_markups.exclude(pk__in=markups_to_be_deleted or []),
            0
        ) + functools.reduce(
            lambda current, child: current + (child.actual or 0),
            children,
            0
        )

    def estimate(self, markups_to_be_deleted=None):
        children = self.children.all()
        self.accumulate_value(children=children)
        self.accumulate_fringe_contribution(children=children)
        self.accumulate_markup_contribution(
            children=children,
            to_be_deleted=markups_to_be_deleted
        )
        self.establish_markup_contribution(to_be_deleted=markups_to_be_deleted)


@signals.model(
    flags=['suppress_budget_update'],
    user_field='updated_by',
    track_fields=['actual'],
    dispatch_fields=['group'],
    track_model_history=['identifier', 'description']
)
class BudgetAccount(Account):
    pdf_type = "pdf-account"
    access = models.ManyToManyField(
        to='user.User',
        related_name='accessible_accounts'
    )
    comments = GenericRelation(Comment)
    events = GenericRelation(Event)

    objects = AccountManager()
    TRACK_CREATE_HISTORY = True

    class Meta(Account.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    @property
    def child_instance_cls(self):
        from greenbudget.app.subaccount.models import BudgetSubAccount
        return BudgetSubAccount


@signals.model(
    flags=['suppress_budget_update'],
    user_field='updated_by',
    track_fields=['actual'],
    dispatch_fields=['group']
)
class TemplateAccount(Account):
    objects = AccountManager()

    FIELDS_TO_DERIVE = ('identifier', 'description') + Account.CALCULATED_FIELDS

    class Meta(Account.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    @property
    def child_instance_cls(self):
        from greenbudget.app.subaccount.models import TemplateSubAccount
        return TemplateSubAccount
