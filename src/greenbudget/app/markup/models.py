from model_utils import Choices
from polymorphic.models import PolymorphicModel

from django.db import models

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Markup(PolymorphicModel):
    identifier = models.CharField(null=True, max_length=128)
    description = models.CharField(null=True, max_length=128)
    UNITS = Choices(
        (0, "percent", "Percent"),
        (1, "flat", "Flat"),
    )
    unit = models.IntegerField(choices=UNITS, default=UNITS.percent, null=True)
    rate = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_markups',
        on_delete=models.CASCADE,
        editable=False
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_markups',
        on_delete=models.CASCADE,
        editable=False
    )

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('-created_at', )
        verbose_name = "Markup"
        verbose_name_plural = "Markups"


class BudgetAccountMarkup(Markup):
    parent = models.ForeignKey(
        to='budget.Budget',
        on_delete=models.CASCADE,
        related_name='markups'
    )
    children = models.ManyToManyField(
        to='account.BudgetAccount',
        related_name='markups'
    )

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('-created_at', )
        verbose_name = "Account Markup"
        verbose_name_plural = "Account Markups"

    def __str__(self):
        return "<{cls} identifier={identifier} parent={parent}>".format(
            cls=self.__class__.__name__,
            identifier=self.identifier,
            parent=self.parent.id,
        )


class BudgetSubAccountMarkup(Markup):
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='budgetaccount')
        | models.Q(app_label='subaccount', model='budgetsubaccount')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')
    children = models.ManyToManyField(
        to='subaccount.BudgetSubAccount',
        related_name='markups'
    )

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('-created_at', )
        verbose_name = "Sub Account Markup"
        verbose_name_plural = "Sub Account Markups"

    def __str__(self):
        return "<{cls} identifier={identifier} parent={parent}>".format(
            cls=self.__class__.__name__,
            identifier=self.identifier,
            parent=self.parent.id,
        )
