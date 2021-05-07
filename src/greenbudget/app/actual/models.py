from model_utils import Choices

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError

from greenbudget.app.comment.models import Comment


class Actual(models.Model):
    type = "actual"
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_actuals',
        on_delete=models.SET_NULL,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_actuals',
        on_delete=models.SET_NULL,
        null=True
    )
    description = models.CharField(null=True, max_length=128)
    vendor = models.CharField(null=True, max_length=128)
    purchase_order = models.CharField(null=True, max_length=128)
    date = models.DateTimeField(null=True)
    # TODO: Should we make this unique across the budget/template?
    payment_id = models.CharField(max_length=50, null=True)
    value = models.FloatField(null=True)
    PAYMENT_METHODS = Choices(
        (0, "check", "Check"),
        (1, "card", "Card"),
        (2, "wire", "Wire"),
    )
    payment_method = models.IntegerField(choices=PAYMENT_METHODS, null=True)
    budget = models.ForeignKey(
        to='budget.Budget',
        on_delete=models.CASCADE,
        related_name='actuals'
    )
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='BudgetAccount')
        | models.Q(app_label='subaccount', model='BudgetSubAccount')
    )
    object_id = models.PositiveIntegerField()
    parent = GenericForeignKey('content_type', 'object_id')
    comments = GenericRelation(Comment)

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('created_at', )
        verbose_name = "Actual"
        verbose_name_plural = "Actual"

    def __str__(self):
        return "<{cls} id={id}, value={value}, content_type={content_type}>".format(  # noqa
            cls=self.__class__.__name__,
            id=self.pk,
            content_type=self.content_type.model,
            value=self.value,
        )

    @property
    def parent_type(self):
        from greenbudget.app.account.models import Account
        if isinstance(self.parent, Account):
            return "account"
        return "subaccount"

    def save(self, *args, **kwargs):
        if self.parent.budget != self.budget:
            raise IntegrityError(
                "The actual must belong to the same budget as it's parent.")
        setattr(self, '_suppress_budget_update',
            kwargs.pop('suppress_budget_update', False))
        return super().save(*args, **kwargs)
