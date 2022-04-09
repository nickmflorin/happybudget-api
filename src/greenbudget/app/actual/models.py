from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError
from django.utils.translation import gettext_lazy as _

from greenbudget.lib.django_utils.models import Choices

from greenbudget.app import model
from greenbudget.app.budgeting.models import BudgetingOrderedRowModel
from greenbudget.app.integrations.plaid.models import PLAID_TRANSACTION_TYPES
from greenbudget.app.tagging.models import Tag

from .managers import ActualManager


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

    PLAID_TRANSACTION_TYPES = PLAID_TRANSACTION_TYPES
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

    IMPORT_SOURCES = Choices((0, "bank_account", "Bank Account"), )

    table_pivot = ('budget_id', )
    domain = 'budget'

    class Meta:
        get_latest_by = "order"
        ordering = ('order', )
        verbose_name = "Actual"
        verbose_name_plural = "Actual"
        unique_together = (('budget', 'order'))

    def __str__(self):
        return str(self.name) or "----"

    def validate_before_save(self):
        try:
            budget = self.budget
        except Actual.budget.RelatedObjectDoesNotExist:
            pass
        else:
            if self.owner is not None and self.owner.budget != budget:
                raise IntegrityError(
                    "Can only add actuals with the same parent as the instance.")
            elif self.contact is not None \
                    and self.contact.created_by != self.created_by:
                raise IntegrityError(
                    "Cannot assign a contact created by one user to an actual "
                    "created by another user."
                )
        super().validate_before_save()

    @classmethod
    def from_plaid_transaction(cls, transaction, **kwargs):
        actual_type = None
        if transaction.transaction_type_classification is not None:
            pttype = transaction.transaction_type_classification
            actual_type = ActualType.objects.get(plaid_transaction_type=pttype)
        return cls(
            name=transaction.name[:50],
            notes=', '.join(transaction.categories),
            date=transaction.date,
            value=transaction.amount,
            actual_type=actual_type,
            **kwargs
        )
