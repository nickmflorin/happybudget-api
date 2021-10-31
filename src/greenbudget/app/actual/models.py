from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from greenbudget.app import signals
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

    class Meta:
        get_latest_by = "created_at"
        ordering = ("order",)
        verbose_name = "Actual Type"
        verbose_name_plural = "Actual Types"

    def __str__(self):
        color_string = None if self.color is None else self.color.code
        return "{title}: {color}".format(
            color=color_string,
            title=self.title
        )


@signals.model(user_field='updated_by')
class Actual(models.Model):
    type = "actual"
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_actuals',
        on_delete=models.CASCADE,
        editable=False
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_actuals',
        on_delete=models.CASCADE,
        editable=False
    )
    name = models.CharField(null=True, max_length=128)
    notes = models.CharField(null=True, max_length=256)
    contact = models.ForeignKey(
        to='contact.Contact',
        null=True,
        on_delete=models.SET_NULL,
        related_name='assigned_actuals'
    )
    attachments = models.ManyToManyField(
        to='io.Attachment',
        related_name='actuals'
    )
    purchase_order = models.CharField(null=True, max_length=128)
    date = models.DateTimeField(null=True)
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

    FIELDS_TO_DUPLICATE = (
        'purchase_order', 'name', 'date', 'payment_id', 'value',
        'actual_type', 'notes'
    )

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('created_at', )
        verbose_name = "Actual"
        verbose_name_plural = "Actual"

    def __str__(self):
        return "Actual: %s" % self.value
