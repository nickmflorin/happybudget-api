import functools
from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from greenbudget.lib.django_utils.models import optional_commit

from greenbudget.app import signals
from greenbudget.app.budgeting.models import use_children
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

    @optional_commit(["accumulated_value"])
    @use_children(["accumulated_value", "rate", "quantity", "multiplier"])
    def accumulate_value(self, children, **kwargs):
        self.accumulated_value = functools.reduce(
            lambda current, sub: current + sub.nominal_value,
            children,
            0
        )

    @optional_commit(["accumulated_markup_contribution"])
    @use_children(["accumulated_markup_contribution", "markup_contribution"])
    def accumulate_markup_contribution(self, children, **kwargs):
        self.accumulated_markup_contribution = functools.reduce(
            lambda current, sub: current + sub.markup_contribution
            + sub.accumulated_markup_contribution,
            children,
            0
        )

    @optional_commit(["accumulated_fringe_contribution"])
    @use_children(["accumulated_fringe_contribution", "fringe_contribution"])
    def accumulate_fringe_contribution(self, children, **kwargs):
        self.accumulated_fringe_contribution = functools.reduce(
            lambda current, sub: current + sub.fringe_contribution
            + sub.accumulated_fringe_contribution,
            children,
            0
        )

    @optional_commit(["markup_contribution"])
    def establish_markup_contribution(self, markups_to_be_deleted=None):
        markups = self.markups.exclude(pk__in=markups_to_be_deleted or [])
        # Markups are applied after the Fringes are applied to the value.
        self.markup_contribution = contribution_from_markups(
            value=self.realized_value,
            markups=markups
        )

    @optional_commit(["actual"])
    @use_children(["actual"])
    def actualize(self, children, markups_to_be_deleted=None, **kwargs):
        markups = self.children_markups.exclude(
            pk__in=markups_to_be_deleted or [])
        # Even though we delete Markup(s) that do not have any children, there
        # is still an edge case where the child-less Markup can still exist at
        # this point.
        markups = [m for m in markups if not m.is_empty]
        self.actual = functools.reduce(
            lambda current, child: current + (child.actual or 0),
            children,
            0
        ) + functools.reduce(
            lambda current, markup: current + (markup.actual or 0),
            markups,
            0
        )

    @optional_commit(list(ESTIMATED_FIELDS))
    def estimate(self, markups_to_be_deleted=None, **kwargs):
        children = self.children.only(*ESTIMATED_FIELDS) \
            .exclude(pk__in=kwargs.get('children_to_be_deleted') or []).all()
        self.accumulate_value(children=children, **kwargs)
        self.accumulate_fringe_contribution(children=children, **kwargs)
        self.accumulate_markup_contribution(children=children, **kwargs)
        self.establish_markup_contribution(
            markups_to_be_deleted=markups_to_be_deleted)


@signals.model(
    flags=['suppress_budget_update'],
    user_field='updated_by',
    exclude_fields=['updated_by', 'created_by'] + list(CALCULATED_FIELDS)
)
class BudgetAccount(Account):
    pdf_type = "pdf-account"
    access = models.ManyToManyField(
        to='user.User',
        related_name='accessible_accounts'
    )
    comments = GenericRelation(Comment)
    events = GenericRelation(Event)

    TRACK_MODEL_HISTORY = True
    TRACK_FIELD_CHANGE_HISTORY = ['identifier', 'description']

    objects = AccountManager()

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
    exclude_fields=['updated_by', 'created_by'] + list(CALCULATED_FIELDS)
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
