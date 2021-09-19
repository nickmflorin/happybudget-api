import functools
from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from greenbudget.lib.django_utils.models import optional_commit
from greenbudget.app import signals

from greenbudget.app.comment.models import Comment
from greenbudget.app.group.models import Group
from greenbudget.app.history.models import Event
from greenbudget.app.markup.utils import contribution_from_markups
from greenbudget.app.subaccount.models import (
    SubAccount, BudgetSubAccount, TemplateSubAccount)

from .managers import AccountManager


def use_subaccounts(fields):
    def decorator(func):
        @functools.wraps(func)
        def inner(instance, *args, **kwargs):
            kwargs['subaccounts'] = kwargs.get('subaccounts')
            if kwargs['subaccounts'] is None:
                kwargs['subaccounts'] = instance.children.exclude(
                    pk__in=kwargs.get('subaccounts_to_be_deleted', []) or []
                ).only(*fields).all()
            func(instance, *args, **kwargs)
        return inner
    return decorator


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
    actual = models.FloatField(default=0.0)
    estimated = models.FloatField(default=0.0)
    fringe_contribution = models.FloatField(default=0.0)
    markup_contribution = models.FloatField(default=0.0)

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

    objects = AccountManager()
    non_polymorphic = models.Manager()

    FIELDS_TO_DUPLICATE = (
        'identifier', 'description', 'actual', 'estimated',
        'fringe_contribution', 'markup_contribution'
    )

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
    def fringed_estimated(self):
        return self.estimated + self.fringe_contribution

    @property
    def real_estimated(self):
        return self.fringed_estimated + self.markup_contribution

    @optional_commit(['estimated'])
    @use_subaccounts(["estimated"])
    def establish_estimated(self, subaccounts, **kwargs):
        self.estimated = functools.reduce(
            lambda current, sub: current + sub.estimated,
            subaccounts,
            0
        )

    @optional_commit(['actual'])
    @use_subaccounts(["actual"])
    def establish_actual(self, subaccounts, **kwargs):
        self.actual = functools.reduce(
            lambda current, sub: current + sub.actual,
            subaccounts,
            0
        )

    @optional_commit(['fringe_contribution'])
    @use_subaccounts(["fringe_contribution"])
    def establish_fringe_contribution(self, subaccounts, **kwargs):
        self.fringe_contribution = functools.reduce(
            lambda current, sub: current + sub.fringe_contribution,
            subaccounts,
            0
        )

    @optional_commit(['markup_contribution'])
    @use_subaccounts(["markup_contribution"])
    def establish_markup_contribution(self, subaccounts, **kwargs):
        markups = self.markups.exclude(
            pk__in=kwargs.get('markups_to_be_deleted', []) or [])

        # Markups are applied after the Fringes are applied to the value.
        self.markup_contribution = contribution_from_markups(
            value=self.fringed_estimated,
            markups=markups
        ) + functools.reduce(
            lambda current, sub: current + sub.markup_contribution,
            subaccounts,
            0
        )

    @optional_commit(['markup_contribution', 'fringe_contribution'])
    @use_subaccounts(['markup_contribution', 'fringe_contribution'])
    def establish_contributions(self, subaccounts, **kwargs):
        self.establish_fringe_contribution(subaccounts=subaccounts)
        # Markups are applied after the Fringes are applied to the value.
        self.establish_markup_contribution(subaccounts=subaccounts, **kwargs)

    @optional_commit(['markup_contribution', 'fringe_contribution', 'estimated'])
    def establish_all(self, **kwargs):
        subaccounts = self.children.only(
            'markup_contribution', 'fringe_contribution', 'estimated') \
                .exclude(pk__in=kwargs.get('subaccounts_to_be_deleted') or []) \
                .all()
        self.establish_estimated(subaccounts=subaccounts)
        self.establish_contributions(subaccounts=subaccounts, **kwargs)


@signals.model(
    flags=['suppress_budget_update'],
    user_field='updated_by',
    exclude_fields=['updated_by', 'created_by', 'estimated', 'actual']
)
class BudgetAccount(Account):
    child_instance_cls = BudgetSubAccount

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


@signals.model(
    flags=['suppress_budget_update'],
    user_field='updated_by',
    exclude_fields=['updated_by', 'created_by', 'estimated']
)
class TemplateAccount(Account):
    child_instance_cls = TemplateSubAccount
    objects = AccountManager()

    FIELDS_TO_DERIVE = ('identifier', 'description', 'estimated')

    class Meta(Account.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
