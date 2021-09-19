import functools
from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError

from greenbudget.lib.django_utils.models import optional_commit
from greenbudget.app import signals

from greenbudget.app.comment.models import Comment
from greenbudget.app.fringe.utils import contribution_from_fringes
from greenbudget.app.group.models import Group
from greenbudget.app.history.models import Event
from greenbudget.app.markup.utils import contribution_from_markups
from greenbudget.app.tagging.models import Tag

from .managers import SubAccountManager


class SubAccountUnit(Tag):
    color = models.ForeignKey(
        to="tagging.Color",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to=models.Q(
            content_types__model="subaccountunit",
            content_types__app_label="subaccount"
        ))

    class Meta:
        get_latest_by = "created_at"
        ordering = ("order",)
        verbose_name = "Sub Account Unit"
        verbose_name_plural = "Sub Account Units"

    def __str__(self):
        color_string = None if self.color is None else self.color.code
        return "{title}: {color}".format(
            color=color_string,
            title=self.title
        )


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


class SubAccount(PolymorphicModel):
    type = "subaccount"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    identifier = models.CharField(null=True, max_length=128)
    description = models.CharField(null=True, max_length=128)
    quantity = models.IntegerField(null=True)
    rate = models.FloatField(null=True)
    multiplier = models.IntegerField(null=True)
    actual = models.FloatField(default=0.0)
    estimated = models.FloatField(default=0.0)
    fringe_contribution = models.FloatField(default=0.0)
    markup_contribution = models.FloatField(default=0.0)

    unit = models.ForeignKey(
        to='subaccount.SubAccountUnit',
        on_delete=models.SET_NULL,
        null=True
    )
    fringes = models.ManyToManyField(to='fringe.Fringe')
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_subaccounts',
        on_delete=models.CASCADE,
        editable=False
    )
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_subaccounts',
        on_delete=models.CASCADE,
        editable=False
    )
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='Account')
        | models.Q(app_label='subaccount', model='SubAccount')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')
    children = GenericRelation('self')
    markups = models.ManyToManyField(
        to='markup.Markup',
        related_name='subaccounts'
    )
    group = models.ForeignKey(
        to='group.Group',
        null=True,
        on_delete=models.SET_NULL,
        related_name='subaccounts'
    )
    groups = GenericRelation(Group)

    objects = SubAccountManager()
    non_polymorphic = models.Manager()

    DERIVING_FIELDS = ("quantity", "rate", "multiplier", "unit")
    FIELDS_TO_DUPLICATE = (
        'identifier', 'description', 'rate', 'quantity', 'multiplier',
        'unit', 'fringe_contribution', 'estimated', 'markup_contribution')

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('created_at', )
        verbose_name = "Sub Account"
        verbose_name_plural = "Sub Accounts"

    @property
    def parent_instance_cls(self):
        return type(self.parent)

    @property
    def siblings(self):
        return self.parent.children.exclude(pk=self.pk).all()

    @property
    def ancestors(self):
        return self.parent.ancestors + [self.parent]

    @property
    def parent_type(self):
        return self.parent.type

    @property
    def budget(self):
        from greenbudget.app.budget.models import BaseBudget
        parent = self.parent
        while not isinstance(parent, BaseBudget):
            parent = parent.parent
        return parent

    @property
    def account(self):
        from greenbudget.app.account.models import Account
        parent = self.parent
        while not isinstance(parent, Account):
            parent = parent.parent
        return parent

    @property
    def raw_estimated_value(self):
        multiplier = self.multiplier or 1.0
        if self.quantity is not None and self.rate is not None:
            return float(self.quantity) * float(self.rate) * float(multiplier)
        return 0.0

    @property
    def fringed_estimated(self):
        return self.estimated + self.fringe_contribution

    @property
    def real_estimated(self):
        return self.fringed_estimated + self.markup_contribution

    @optional_commit(["estimated"])
    @use_subaccounts(["estimated"])
    def establish_estimated(self, subaccounts, **kwargs):
        if len(subaccounts) == 0:
            self.estimated = self.raw_estimated_value
        else:
            self.estimated = functools.reduce(
                lambda current, sub: current + sub.estimated,
                subaccounts,
                0
            )

    @optional_commit(["actual"])
    @use_subaccounts(["actual"])
    def establish_actual(self, subaccounts, **kwargs):
        actuals = self.actuals.exclude(
            pk__in=kwargs.get('actuals_to_be_deleted', []) or [])

        self.actual = functools.reduce(
            lambda current, sub: current + sub.actual,
            subaccounts,
            0
        ) + functools.reduce(
            lambda current, actual: current + (actual.value or 0),
            actuals,
            0
        )

    @optional_commit(["fringe_contribution"])
    @use_subaccounts(["fringe_contribution"])
    def establish_fringe_contribution(self, subaccounts, **kwargs):
        fringes = self.fringes.exclude(
            pk__in=kwargs.get('fringes_to_be_deleted', []) or [])

        self.fringe_contribution = contribution_from_fringes(
            value=self.estimated,
            fringes=fringes
        ) + functools.reduce(
            lambda current, sub: current + sub.fringe_contribution,
            subaccounts,
            0
        )

    @optional_commit(["markup_contribution"])
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

    @optional_commit(["markup_contribution", "fringe_contribution"])
    @use_subaccounts(["markup_contribution", "fringe_contribution"])
    def establish_contributions(self, subaccounts, **kwargs):
        self.establish_fringe_contribution(subaccounts=subaccounts, **kwargs)
        # Markups are applied after the Fringes are applied to the value.
        self.establish_markup_contribution(subaccounts=subaccounts, **kwargs)

    @optional_commit(["markup_contribution", "fringe_contribution", "estimated"])
    def establish_all(self, **kwargs):
        subaccounts = self.children.only(
            'markup_contribution', 'fringe_contribution', 'estimated') \
                .exclude(pk__in=kwargs.get('subaccounts_to_be_deleted') or []) \
                .all()
        self.establish_estimated(subaccounts=subaccounts, **kwargs)
        self.establish_contributions(subaccounts=subaccounts, **kwargs)


@signals.model(
    flags=['suppress_budget_update'],
    user_field='updated_by',
    exclude_fields=[
        'updated_by', 'created_by', 'estimated', 'actual',
        'fringe_contribution', 'markup_contribution'
    ]
)
class BudgetSubAccount(SubAccount):
    contact = models.ForeignKey(
        to='contact.Contact',
        null=True,
        on_delete=models.SET_NULL,
        related_name='assigned_subaccounts'
    )
    comments = GenericRelation(Comment)
    events = GenericRelation(Event)
    objects = SubAccountManager()

    TRACK_MODEL_HISTORY = True
    TRACK_FIELD_CHANGE_HISTORY = (
        'identifier', 'description', 'rate', 'quantity', 'multiplier',
        'unit')
    DERIVING_FIELDS = SubAccount.DERIVING_FIELDS + ("contact", )

    class Meta(SubAccount.Meta):
        verbose_name = "Budget Sub Account"
        verbose_name_plural = "Budget Sub Accounts"

    def __str__(self):
        return "Budget Sub Account: %s" % self.identifier

    def save(self, *args, **kwargs):
        # TODO: Use signals to validate this.
        if self.contact is not None and self.contact.user != self.created_by:
            raise IntegrityError(
                "Cannot assign a contact created by one user to a sub account "
                "created by another user."
            )
        return super().save(*args, **kwargs)


@signals.model(
    flags=['suppress_budget_update'],
    user_field='updated_by',
    exclude_fields=[
        'updated_by', 'created_by', 'estimated', 'fringe_contribution',
        'markup_contribution'
    ]
)
class TemplateSubAccount(SubAccount):
    objects = SubAccountManager()

    FIELDS_TO_DERIVE = SubAccount.FIELDS_TO_DUPLICATE

    class Meta(SubAccount.Meta):
        verbose_name = "Template Sub Account"
        verbose_name_plural = "Template Sub Accounts"

    def __str__(self):
        return "Template Sub Account: %s" % self.identifier
