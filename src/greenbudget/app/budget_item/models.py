from polymorphic.models import PolymorphicModel

from django.db import models


class BudgetItem(PolymorphicModel):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_sub_accounts',
        on_delete=models.SET_NULL,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_sub_accounts',
        on_delete=models.SET_NULL,
        null=True
    )
    identifier = models.CharField(max_length=128)
    description = models.CharField(null=True, max_length=128)
    # TODO: We need to build in constraints for sub accounts such that the
    # budget that the subaccount parent belongs to is the same as the budget
    # that the subaccount belongs to.
    budget = models.ForeignKey(
        to='budget.Budget',
        related_name="items",
        on_delete=models.CASCADE,
        db_index=True,
    )

    class Meta:
        get_latest_by = "updated_at"
        # Since the data from this model is used to power AGGridReact tables,
        # we want to keep the ordering of the accounts consistent.
        ordering = ('created_at', )
        verbose_name = "Budget Item"
        verbose_name_plural = "Budget Items"
        unique_together = (('budget', 'identifier'), )

    @property
    def variance(self):
        if self.actual is not None and self.estimated is not None:
            return self.estimated - self.actual
        return None

    @property
    def actual(self):
        actuals = []
        for actual in self.actuals.all():
            if actual.value is not None:
                actuals.append(actual.value)
        if len(actuals) != 0:
            return sum(actuals)
        return None
