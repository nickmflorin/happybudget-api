from model_utils import Choices

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, IntegrityError

from greenbudget.app import signals
from greenbudget.app.comment.models import Comment

from .managers import ActualManager


@signals.model(
    flags=['suppress_budget_update'],
    user_field='updated_by',
    exclude_fields=['updated_by', 'created_by']
)
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
    description = models.CharField(null=True, max_length=128)
    vendor = models.CharField(null=True, max_length=128)
    purchase_order = models.CharField(null=True, max_length=128)
    date = models.DateTimeField(null=True)
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
    subaccount = models.ForeignKey(
        to='subaccount.BudgetSubAccount',
        on_delete=models.CASCADE,
        related_name="actuals",
        null=True
    )
    comments = GenericRelation(Comment)
    objects = ActualManager()

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('created_at', )
        verbose_name = "Actual"
        verbose_name_plural = "Actual"

    def __str__(self):
        return "<{cls} id={id}, value={value}, subaccount={subaccount}>".format(  # noqa
            cls=self.__class__.__name__,
            id=self.pk,
            value=self.value,
            subaccount=self.subaccount.pk if self.subaccount is not None else None  # noqa
        )

    def save(self, *args, **kwargs):
        subaccount_budget = None
        if self.subaccount is not None:
            subaccount_budget = self.subaccount.budget

        if subaccount_budget is not None and self.budget is not None \
                and subaccount_budget != self.budget:
            raise IntegrityError(
                "The actual must belong to the same budget as it's subaccount.")

        return super().save(*args, **kwargs)
