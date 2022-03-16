import copy

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError
from django.utils.functional import cached_property

from greenbudget.lib.utils import cumulative_sum

from greenbudget.app import model, signals
from greenbudget.app.actual.models import Actual
from greenbudget.app.budgeting.models import (
    BudgetingTreePolymorphicOrderedRowModel, AssociatedModel,
    children_method_handler)
from greenbudget.app.fringe.utils import contribution_from_fringes
from greenbudget.app.group.models import Group
from greenbudget.app.markup.models import Markup
from greenbudget.app.markup.utils import contribution_from_markups
from greenbudget.app.tagging.models import Tag

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


class SubAccount(BudgetingTreePolymorphicOrderedRowModel):
    quantity = models.FloatField(null=True, blank=True)
    rate = models.FloatField(null=True, blank=True)
    multiplier = models.IntegerField(null=True, blank=True)
    fringe_contribution = models.FloatField(default=0.0)
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
    is_deleting = models.BooleanField(default=False)

    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')
    children = GenericRelation('self')
    groups = GenericRelation(Group)
    actuals = GenericRelation(Actual)
    children_markups = GenericRelation(Markup)

    objects = SubAccountManager()
    non_polymorphic = models.Manager()

    table_pivot = ('content_type_id', 'object_id')
    child_instance_cls = AssociatedModel('self')
    DERIVING_FIELDS = ("quantity", "rate", "multiplier", "unit")
    ESTIMATED_FIELDS = ESTIMATED_FIELDS
    CALCULATED_FIELDS = CALCULATED_FIELDS
    VALID_PARENTS = ['account_cls', 'subaccount_cls']

    class Meta:
        get_latest_by = "order"
        ordering = ('order', )
        verbose_name = "Sub Account"
        verbose_name_plural = "Sub Accounts"
        unique_together = (('content_type', 'object_id', 'order'))

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
        quantity = self.quantity or 1.0
        if self.rate is not None:
            return float(quantity) * float(self.rate) * float(multiplier)
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

    def will_change_parent_estimation(self, action):
        """
        Returns whether or not the :obj:`SubAccount` instance will change the
        estimated values of it's parent after it is updated, created or deleted.
        """
        self.actions.validate(action)
        if action == self.actions.CREATE:
            # When creating :obj:`SubAccount` instance(s), the only way that
            # they have an estimated value and affect the parent's estimated
            # value will be if the rate and quantity field are non-null.  This
            # is because a :obj:`SubAccount` cannot be assigned children,
            return self.rate not in (None, 0.0) \
                and self.quantity not in (None, 0.0)
        elif action == self.actions.DELETE:
            if self.children.count() != 0:
                return any([metric != 0.0 for metric in [
                    self.fringe_contribution,
                    self.accumulated_fringe_contribution,
                    self.markup_contribution,
                    self.accumulated_markup_contribution,
                    self.accumulated_value
                ]])
            return self.raw_value != 0.0
        else:
            return self.fields_have_changed('multiplier', 'quantity', 'rate')

    @children_method_handler
    def accumulate_value(self, children):
        previous_value = self.accumulated_value
        self.accumulated_value = cumulative_sum(children, attr='nominal_value')
        return previous_value != self.accumulated_value

    @children_method_handler
    def accumulate_markup_contribution(self, children, to_be_deleted=None):
        markups = self.children_markups.filter(unit=Markup.UNITS.flat).exclude(
            pk__in=to_be_deleted or [],
        )
        previous_value = self.accumulated_markup_contribution
        self.accumulated_markup_contribution = cumulative_sum(
            children,
            attr=['markup_contribution', 'accumulated_markup_contribution']
        ) + cumulative_sum(markups, attr='rate', ignore_values=None)
        return previous_value != self.accumulated_markup_contribution

    @children_method_handler
    def accumulate_fringe_contribution(self, children):
        previous_value = self.accumulated_fringe_contribution
        self.accumulated_fringe_contribution = cumulative_sum(
            children,
            attr=['fringe_contribution', 'accumulated_fringe_contribution']
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

    def calculate(self, *args, **kwargs):
        return self.estimate(*args, **kwargs)

    @signals.disable()
    def clear_deriving_fields(self, commit=True):
        for field in self.DERIVING_FIELDS:
            setattr(self, field, None)
        # M2M fields must be updated immediately, regardless of whether or not
        # we are committing.
        self.fringes.set([])
        if commit:
            self.save(update_fields=self.DERIVING_FIELDS)

    @children_method_handler
    def estimate(self, children, **kwargs):
        markups_to_be_deleted = kwargs.get('markups_to_be_deleted', [])
        alterations = [
            self.accumulate_value(children),
            self.accumulate_fringe_contribution(children),
            self.accumulate_markup_contribution(
                children,
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
                self.save()
            if kwargs.get('trickle', True):
                self.parent.estimate(
                    unsaved_children=unsaved_recursive_children,
                    **kwargs
                )
        return any(alterations)


@model.model(user_field='updated_by', type='subaccount')
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

    pdf_type = 'pdf-subaccount'
    domain = "budget"

    class Meta(SubAccount.Meta):
        verbose_name = "Budget Sub Account"
        verbose_name_plural = "Budget Sub Accounts"

    def validate_before_save(self):
        super().validate_before_save()
        if self.contact is not None \
                and self.contact.created_by != self.created_by:
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

    @children_method_handler
    def actualize(self, children, **kwargs):
        markups_to_be_deleted = kwargs.get('markups_to_be_deleted', []) or []
        actuals_to_be_deleted = kwargs.pop('actuals_to_be_deleted', []) or []
        previous_value = self.actual
        self.actual = cumulative_sum(children, attr='actual') + cumulative_sum(
            self.children_markups.exclude(pk__in=markups_to_be_deleted),
            attr='actual',
        ) + cumulative_sum(
            self.actuals.exclude(pk__in=actuals_to_be_deleted),
            attr='value',
            ignore_values=None
        )
        if previous_value != self.actual:
            unsaved = [self]
            if kwargs.get('commit', False):
                unsaved = None
                self.save(update_fields=['actual'])

            if kwargs.get('trickle', True):
                parent_actualization_kwargs = copy.deepcopy(kwargs)
                parent_actualization_kwargs.update(unsaved_children=unsaved)
                # The actuals only contribute to the actual value directly if
                # the parent is a SubAccount.
                if isinstance(self.parent, BudgetSubAccount):
                    parent_actualization_kwargs.update(
                        actuals_to_be_deleted=actuals_to_be_deleted
                    )
                self.parent.actualize(**parent_actualization_kwargs)
        return previous_value != self.actual


@model.model(user_field='updated_by', type='subaccount')
class TemplateSubAccount(SubAccount):
    domain = "template"
    objects = TemplateSubAccountManager()

    class Meta(SubAccount.Meta):
        verbose_name = "Template Sub Account"
        verbose_name_plural = "Template Sub Accounts"
