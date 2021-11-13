import functools

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError
from django.utils.functional import cached_property

from greenbudget.app import signals
from greenbudget.app.actual.models import Actual
from greenbudget.app.budgeting.models import BudgetingTreePolymorphicModel
from greenbudget.app.fringe.utils import contribution_from_fringes
from greenbudget.app.group.models import Group
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.utils import contribution_from_markups
from greenbudget.app.tagging.models import Tag

from .cache import (
    subaccount_markups_cache,
    subaccount_groups_cache,
    subaccount_detail_cache,
    subaccount_subaccounts_cache
)
from .managers import (
    SubAccountManager,
    BudgetSubAccountManager,
    TemplateSubAccountManager
)


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


class SubAccount(BudgetingTreePolymorphicModel):
    type = "subaccount"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
    identifier = models.CharField(null=True, max_length=128)
    description = models.CharField(null=True, max_length=128)
    quantity = models.FloatField(null=True)
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
    fringes = models.ManyToManyField(
        to='fringe.Fringe',
        related_name='subaccounts'
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
    children_markups = GenericRelation(Markup)

    objects = SubAccountManager()
    non_polymorphic = models.Manager()

    DERIVING_FIELDS = ("quantity", "rate", "multiplier", "unit")

    CACHES = [
        subaccount_markups_cache,
        subaccount_groups_cache,
        subaccount_detail_cache,
        subaccount_subaccounts_cache
    ]

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
        parent = self.parent
        while hasattr(parent, 'parent'):
            parent = parent.parent
        return parent

    @property
    def account(self):
        parent = self.parent
        while True:
            if not hasattr(parent, 'parent'):
                break
            parent = parent.parent
        return parent

    @cached_property
    def nested_level(self):
        level = 0
        parent = self.parent
        while hasattr(parent, 'parent'):
            parent = parent.parent
            level = level + 1
        return level - 1

    @property
    def raw_value(self):
        multiplier = self.multiplier or 1.0
        if self.quantity is not None and self.rate is not None:
            return float(self.quantity) * float(self.rate) * float(multiplier)
        return 0.0

    @property
    def raw_value_changed(self):
        return self.fields_have_changed('multiplier', 'quantity', 'rate')

    @property
    def nominal_value(self):
        if self.children.count() == 0:
            return self.raw_value
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
        previous_value = self.accumulated_markup_contribution
        self.accumulated_markup_contribution = functools.reduce(
            lambda current, sub: current + sub.markup_contribution
            + sub.accumulated_markup_contribution,
            children,
            0
        ) + functools.reduce(
            lambda current, markup: current + markup.rate,
            markups.exclude(pk__in=to_be_deleted or []),
            0
        )
        return previous_value != self.accumulated_markup_contribution

    def accumulate_fringe_contribution(self, children=None):
        children = children or self.children.all()
        previous_value = self.accumulated_fringe_contribution
        self.accumulated_fringe_contribution = functools.reduce(
            lambda current, sub: current + sub.fringe_contribution
            + sub.accumulated_fringe_contribution,
            children,
            0
        )
        return previous_value != self.accumulate_fringe_contribution

    def establish_fringe_contribution(self, to_be_deleted=None):
        previous_value = self.fringe_contribution
        self.fringe_contribution = contribution_from_fringes(
            value=self.realized_value,
            fringes=self.fringes.exclude(pk__in=to_be_deleted or [])
        )
        return previous_value != self.fringe_contribution

    def establish_markup_contribution(self, to_be_deleted=None):
        previous_value = self.markup_contribution
        self.markup_contribution = contribution_from_markups(
            value=self.realized_value + self.fringe_contribution,
            markups=self.markups.exclude(pk__in=to_be_deleted or [])
        )
        return previous_value != self.markup_contribution

    def calculate(self, **kwargs):
        return self.estimate(**kwargs)

    @signals.disable()
    def clear_deriving_fields(self, commit=True):
        for field in self.DERIVING_FIELDS:
            setattr(self, field, None)
        # M2M fields must be updated immediately, regardless of whether or not
        # we are committing.
        self.fringes.set([])
        if commit:
            self.save(update_fields=self.DERIVING_FIELDS)

    def estimate(self, **kwargs):
        children, kwargs = self.children_from_kwargs(**kwargs)
        markups_to_be_deleted = kwargs.get('markups_to_be_deleted', [])

        alterations = [
            self.accumulate_value(children=children),
            self.accumulate_fringe_contribution(children=children),
            self.accumulate_markup_contribution(
                children=children,
                to_be_deleted=markups_to_be_deleted
            ),
            # Because Fringes are a M2M field on the instance, the instance
            # needs to be saved before it can be used.
            self.establish_fringe_contribution(
                to_be_deleted=kwargs.pop('fringes_to_be_deleted', [])
            ),
            # Markups are applied after the Fringes are applied to the value.
            # Because Markups are a M2M field on the instance, the instance
            # needs to be saved before it can be used.
            self.establish_markup_contribution(
                to_be_deleted=markups_to_be_deleted
            )
        ]
        if any(alterations):
            unsaved_recursive_children = [self]
            if kwargs.get('commit', False):
                unsaved_recursive_children = None
                self.save(update_fields=self.reestimated_fields)

            # There are cases with CASCADE deletes where a non-nullable field
            # will be temporarily null.
            if kwargs.get('trickle', True) and self.parent is not None:
                self.parent.estimate(
                    unsaved_children=unsaved_recursive_children,
                    **kwargs
                )
        return any(alterations)


@signals.model(user_field='updated_by')
class BudgetSubAccount(SubAccount):
    attachments = models.ManyToManyField(
        to='io.Attachment',
        related_name='subaccounts'
    )
    contact = models.ForeignKey(
        to='contact.Contact',
        null=True,
        on_delete=models.SET_NULL,
        related_name='assigned_subaccounts'
    )
    objects = BudgetSubAccountManager()

    DERIVING_FIELDS = SubAccount.DERIVING_FIELDS + ("contact", )
    associated = [
        ('budget', 'budget'),
        ('account', 'budgetaccount'),
        ('subaccount', 'budgetsubaccount')
    ]
    pdf_type = 'pdf-subaccount'
    domain = "budget"

    class Meta(SubAccount.Meta):
        verbose_name = "Budget Sub Account"
        verbose_name_plural = "Budget Sub Accounts"

    def __str__(self):
        return "Budget Sub Account: %s" % self.identifier

    def validate_before_save(self):
        super().validate_before_save()
        if self.contact is not None \
                and self.contact.user != self.created_by:
            raise IntegrityError(
                "Cannot assign a contact created by one user to a sub account "
                "created by another user."
            )

    @signals.disable()
    def clear_deriving_fields(self, commit=True):
        super().clear_deriving_fields(commit=False)
        for field in self.DERIVING_FIELDS:
            setattr(self, field, None)
        self.attachments.set([])
        if commit:
            self.save(update_fields=self.DERIVING_FIELDS)

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

    def actualize(self, **kwargs):
        children, kwargs = self.children_from_kwargs(**kwargs)
        markups_to_be_deleted = kwargs.get('markups_to_be_deleted', []) or []

        previous_value = self.actual
        self.actual = functools.reduce(
            lambda current, child: current + (child.actual or 0),
            children,
            0
        ) + functools.reduce(
            lambda current, markup: current + (markup.actual or 0),
            self.children_markups.exclude(pk__in=markups_to_be_deleted or []),
            0
        ) + functools.reduce(
            lambda current, actual: current + (actual.value or 0),
            self.actuals.all(),
            0
        )
        if previous_value != self.actual:
            unsaved_recursive_children = [self]
            if kwargs.get('commit', False):
                unsaved_recursive_children = None
                self.save(update_fields=['actual'])
            # There are cases with CASCADE deletes where a non-nullable field
            # will be temporarily null.
            if kwargs.get('trickle', True) and self.parent is not None:
                self.parent.actualize(
                    unsaved_children=unsaved_recursive_children,
                    **kwargs
                )
        return previous_value != self.actual


@signals.model(user_field='updated_by')
class TemplateSubAccount(SubAccount):
    domain = "template"
    associated = [
        ('template', 'template'),
        ('account', 'templateaccount'),
        ('subaccount', 'templatesubaccount')
    ]
    objects = TemplateSubAccountManager()

    class Meta(SubAccount.Meta):
        verbose_name = "Template Sub Account"
        verbose_name_plural = "Template Sub Accounts"

    def __str__(self):
        return "Template Sub Account: %s" % self.identifier
