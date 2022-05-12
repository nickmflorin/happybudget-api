import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError
from django.utils.translation import gettext_lazy as _

from happybudget.lib.django_utils.models import (
    Choices, generic_fk_instance_change)

from happybudget.app import model
from happybudget.app.budgeting.models import BudgetingOrderedRowModel
from happybudget.app.tagging.models import Tag

from .managers import ActualManager


logger = logging.getLogger('happybudget')


class ActualType(Tag):
    color = models.ForeignKey(
        to="tagging.Color",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to=models.Q(
            content_types__model="actualtype",
            content_types__app_label="actual"
        ))

    PLAID_TRANSACTION_TYPES = Choices(
        (0, "credit_card", "Credit Card"),
        (1, "check", "Check"),
        (2, "wire", "Wire"),
        (3, "ach", "ACH"),
    )
    plaid_transaction_type = models.IntegerField(
        choices=PLAID_TRANSACTION_TYPES,
        null=True,
        unique=True,
        help_text=_(
            'Designates which Plaid transaction type should be mapped to '
            'this actual type.'
        ),
    )

    class Meta:
        get_latest_by = "created_at"
        ordering = ("order",)
        verbose_name = "Actual Type"
        verbose_name_plural = "Actual Types"

    def __str__(self):
        color_string = None if self.color is None else self.color.code
        return f"{self.title}: {color_string}"

    @classmethod
    def plaid_transaction_name(cls, transaction_type):
        return cls.PLAID_TRANSACTION_TYPES.get_name(transaction_type)


@model.model(type='actual')
class Actual(BudgetingOrderedRowModel):
    name = models.CharField(null=True, max_length=128)
    notes = models.CharField(null=True, max_length=256)
    contact = models.ForeignKey(
        to='contact.Contact',
        null=True,
        on_delete=models.SET_NULL,
        related_name='tagged_actuals'
    )
    attachments = models.ManyToManyField(
        to='io.Attachment',
        related_name='actuals'
    )
    purchase_order = models.CharField(null=True, max_length=128)
    date = models.DateField(null=True)
    payment_id = models.CharField(max_length=50, null=True)
    value = models.FloatField(null=True)
    actual_type = models.ForeignKey(
        to='actual.ActualType',
        on_delete=models.SET_NULL,
        null=True
    )
    budget = models.ForeignKey(
        to='budget.Budget',
        on_delete=models.CASCADE,
        related_name='actuals'
    )
    content_type = models.ForeignKey(
        to=ContentType,
        null=True,
        on_delete=models.SET_NULL,
        limit_choices_to=models.Q(app_label='markup', model='Markup')
        | models.Q(app_label='subaccount', model='BudgetSubAccount')
    )
    object_id = models.PositiveIntegerField(db_index=True, null=True)
    owner = GenericForeignKey('content_type', 'object_id')
    objects = ActualManager()
    user_ownership_field = 'budget__created_by'

    IMPORT_SOURCES = Choices((0, "bank_account", "Bank Account"), )

    table_pivot = ('budget_id', )
    static_domain = 'budget'

    class Meta:
        get_latest_by = "order"
        ordering = ('order', )
        verbose_name = "Actual"
        verbose_name_plural = "Actual"
        unique_together = (('budget', 'order'))

    def __str__(self):
        return str(self.name) or "----"

    def get_owners_to_reactualize(self, action):
        if action in (self.actions.CREATE, self.actions.DELETE):
            return set([self.owner]) if self.owner is not None else set([])
        owners_to_reactualize = set([])
        # If the Actual is in the midst of being created, we always want
        # to actualize the owners.
        if self._state.adding is True or self.was_just_added():
            if self.owner is not None:
                owners_to_reactualize.add(self.owner)
        else:
            # We only need to reactualize the owner if the owner was changed
            # or the actual value was changed.
            old_owner, new_owner = generic_fk_instance_change(self)
            if old_owner != new_owner:
                owners_to_reactualize.update([
                    x for x in [new_owner, old_owner]
                    if x is not None
                ])
            elif self.field_has_changed('value') and self.owner is not None:
                owners_to_reactualize.add(self.owner)
        return owners_to_reactualize

    def validate_before_save(self):
        if self.contact is not None:
            self.contact.has_same_owner(self, raise_exception=True)
        try:
            budget = self.budget
        except Actual.budget.RelatedObjectDoesNotExist:
            pass
        else:
            if self.owner is not None and self.owner.budget != budget:
                raise IntegrityError(
                    "Can only add actuals with the same parent as the instance.")
        super().validate_before_save()

    @classmethod
    def from_plaid_transaction(cls, transaction, **kwargs):
        actual_type = None
        if transaction.classification is not None:
            try:
                actual_type = ActualType.objects.get(
                    plaid_transaction_type=transaction.classification)
            except ActualType.DoesNotExist:
                # This can happen if the relevant ActualType has not been
                # configured yet.  In this case, we don't want the import to
                # fail - we just want to be aware that the ActualType needs to
                # be configured.
                name = ActualType.plaid_transaction_name(
                    transaction.classification)
                logger.warning(
                    "No actual type is configured for plaid transaction "
                    f"type {name}."
                )
        return cls(
            name=transaction.name[:50],
            notes=', '.join(transaction.categories),
            date=transaction.date,
            value=transaction.amount,
            actual_type=actual_type,
            **kwargs
        )
