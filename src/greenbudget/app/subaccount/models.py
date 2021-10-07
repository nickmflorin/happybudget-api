import functools
from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError

from greenbudget.lib.django_utils.models import optional_commit

from greenbudget.app import signals
from greenbudget.app.actual.models import Actual
from greenbudget.app.budgeting.models import use_children
from greenbudget.app.comment.models import Comment
from greenbudget.app.fringe.utils import contribution_from_fringes
from greenbudget.app.group.models import Group
from greenbudget.app.history.models import Event
from greenbudget.app.markup.models import Markup
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


ESTIMATED_FIELDS = (
    'accumulated_value',
    'fringe_contribution',
    'markup_contribution',
    'accumulated_markup_contribution',
    'accumulated_fringe_contribution'
)
CALCULATED_FIELDS = ESTIMATED_FIELDS + ('actual', )


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

    ESTIMATED_FIELDS = ESTIMATED_FIELDS
    CALCULATED_FIELDS = CALCULATED_FIELDS

    # The sum of the nominal values of all of the children.
    accumulated_value = models.FloatField(default=0.0)
    fringe_contribution = models.FloatField(default=0.0)
    accumulated_fringe_contribution = models.FloatField(default=0.0)
    markup_contribution = models.FloatField(default=0.0)
    accumulated_markup_contribution = models.FloatField(default=0.0)

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
    actuals = GenericRelation(Actual)

    objects = SubAccountManager()
    non_polymorphic = models.Manager()

    DERIVING_FIELDS = ("quantity", "rate", "multiplier", "unit")
    FIELDS_TO_DUPLICATE = ('identifier', 'description') + DERIVING_FIELDS \
        + CALCULATED_FIELDS

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
    def raw_value(self):
        multiplier = self.multiplier or 1.0
        if self.quantity is not None and self.rate is not None:
            return float(self.quantity) * float(self.rate) * float(multiplier)
        return 0.0

    @property
    def nominal_value(self):
        if self.children.count() == 0:
            return self.raw_value
        return self.accumulated_value

    @property
    def realized_value(self):
        return self.nominal_value + self.accumulated_fringe_contribution \
            + self.accumulated_markup_contribution

    @optional_commit(["accumulated_value"])
    @use_children(["accumulated_value"])
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

    @optional_commit(["fringe_contribution"])
    def establish_fringe_contribution(self, fringes_to_be_deleted=None):
        fringes = self.fringes.exclude(pk__in=fringes_to_be_deleted or [])
        self.fringe_contribution = contribution_from_fringes(
            value=self.realized_value,
            fringes=fringes
        )

    @optional_commit(["markup_contribution"])
    def establish_markup_contribution(self, markups_to_be_deleted=None):
        markups = self.markups.exclude(pk__in=markups_to_be_deleted or [])
        # Markups are applied after the Fringes are applied to the value.
        self.markup_contribution = contribution_from_markups(
            value=self.realized_value + self.fringe_contribution,
            markups=markups
        )

    @optional_commit(["actual"])
    @use_children(["actual"])
    def actualize(self, children, markups_to_be_deleted=None, **kwargs):
        markups = self.markups.exclude(pk__in=markups_to_be_deleted or [])
        actuals = self.actuals.exclude(
            pk__in=kwargs.get('actuals_to_be_deleted', []) or []).only('value')
        self.actual = functools.reduce(
            lambda current, child: current + (child.actual or 0),
            children,
            0
        ) + functools.reduce(
            lambda current, markup: current + (markup.actual or 0),
            markups,
            0
        ) + functools.reduce(
            lambda current, actual: current + (actual.value or 0),
            actuals,
            0
        )

    @optional_commit(list(ESTIMATED_FIELDS))
    @use_children(list(ESTIMATED_FIELDS))
    def estimate(self, children, markups_to_be_deleted=None,
            fringes_to_be_deleted=None, **kwargs):
        self.accumulate_value(children=children, **kwargs)
        self.accumulate_fringe_contribution(children=children, **kwargs)
        self.accumulate_markup_contribution(children=children, **kwargs)
        self.establish_fringe_contribution(
            fringes_to_be_deleted=fringes_to_be_deleted)
        self.establish_markup_contribution(
            markups_to_be_deleted=markups_to_be_deleted)


@signals.model(
    flags=['suppress_budget_update'],
    user_field='updated_by',
    exclude_fields=['updated_by', 'created_by'] + list(CALCULATED_FIELDS)
)
class BudgetSubAccount(SubAccount):
    pdf_type = 'pdf-subaccount'

    contact = models.ForeignKey(
        to='contact.Contact',
        null=True,
        on_delete=models.SET_NULL,
        related_name='assigned_subaccounts'
    )
    comments = GenericRelation(Comment)
    events = GenericRelation(Event)
    children_markups = GenericRelation(Markup)

    objects = SubAccountManager()

    TRACK_MODEL_HISTORY = True
    TRACK_FIELD_CHANGE_HISTORY = (
        'identifier', 'description') + SubAccount.DERIVING_FIELDS
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
    exclude_fields=['updated_by', 'created_by'] + list(CALCULATED_FIELDS)
)
class TemplateSubAccount(SubAccount):
    objects = SubAccountManager()

    FIELDS_TO_DERIVE = SubAccount.FIELDS_TO_DUPLICATE

    class Meta(SubAccount.Meta):
        verbose_name = "Template Sub Account"
        verbose_name_plural = "Template Sub Accounts"

    def __str__(self):
        return "Template Sub Account: %s" % self.identifier
