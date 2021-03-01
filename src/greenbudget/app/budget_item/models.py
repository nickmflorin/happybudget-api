from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class BudgetItem(PolymorphicModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.CharField(null=True, max_length=128)
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='budget', model='Budget')
        | models.Q(app_label='budget_item', model='BudgetItem')
    )
    object_id = models.PositiveIntegerField()
    parent = GenericForeignKey('content_type', 'object_id')
    estimated = models.DecimalField(default=0, decimal_places=2, max_digits=21)


class GenericBudgetItem(BudgetItem):
    pass


class QuantityBudgetItem(BudgetItem):
    name = models.CharField(max_length=30, default=None, null=True)
    quantity = models.DecimalField(
        default=None, decimal_places=2, max_digits=10, null=True)
    unit = models.CharField(max_length=20, default=None, null=True)
    rate = models.DecimalField(
        default=None, decimal_places=2, max_digits=10, null=True)
    fringes = models.DecimalField(
        default=None, decimal_places=1, max_digits=5, null=True)
