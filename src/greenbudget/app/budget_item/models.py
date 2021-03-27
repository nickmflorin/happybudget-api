from colorful.fields import RGBColorField
from polymorphic.models import PolymorphicModel

from django.db import models


# Right now, we still need to iron out a discrepancy in the UI: whether or not
# the actuals for parent line items should be determined from the sum of the
# actuals of it's children, or the sum of the actuals tied to the parent.  This
# is a temporary toggle to switch between the two.
DETERMINE_ACCOUNT_ACTUAL_FROM_UNDERLYINGS = True
DETERMINE_SUB_ACCOUNT_ACTUAL_FROM_UNDERLYINGS = False


class BudgetItemGroup(PolymorphicModel):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_groups',
        on_delete=models.SET_NULL,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_groups',
        on_delete=models.SET_NULL,
        null=True
    )
    color = RGBColorField(colors=[
        "#797695",
        "#ff7165",
        "#80cbc4",
        "#ce93d8",
        "#fed835",
        "#c87987",
        "#69f0ae",
        "#a1887f",
        "#81d4fa",
        "#f75776",
        "#66bb6a",
        "#58add6"
    ], default='#EFEFEF')

    class Meta:
        get_latest_by = "created_at"
        ordering = ('created_at', )
        verbose_name = "Budget Item Group"
        verbose_name_plural = "Budget Item Groups"

    @property
    def variance(self):
        if self.actual is not None and self.estimated is not None:
            return float(self.estimated) - float(self.actual)
        return None

    @property
    def actual(self):
        actuals = []
        for child in self.children.all():
            if child.actual is not None:
                actuals.append(child.actual)
        if len(actuals) != 0:
            return sum(actuals)
        return None

    @property
    def estimated(self):
        estimated = []
        for child in self.children.all():
            if child.estimated is not None:
                estimated.append(child.estimated)
        if len(estimated) != 0:
            return sum(estimated)
        return None


class BudgetItem(PolymorphicModel):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_budget_items',
        on_delete=models.SET_NULL,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_budget_items',
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
    group = models.ForeignKey(
        to='budget_item.BudgetItemGroup',
        null=True,
        on_delete=models.SET_NULL,
        related_name='children'
    )

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('created_at', )
        verbose_name = "Budget Item"
        verbose_name_plural = "Budget Items"
        unique_together = (('budget', 'identifier'), )

    @property
    def variance(self):
        if self.actual is not None and self.estimated is not None:
            return float(self.estimated) - float(self.actual)
        return None

    @property
    def actual(self):
        from greenbudget.app.account.models import Account

        actuals = []
        flag = DETERMINE_SUB_ACCOUNT_ACTUAL_FROM_UNDERLYINGS
        if isinstance(self, Account):
            flag = DETERMINE_ACCOUNT_ACTUAL_FROM_UNDERLYINGS

        if flag:
            for subaccount in self.subaccounts.all():
                if subaccount.actual is not None:
                    actuals.append(subaccount.actual)
        else:
            for actual in self.actuals.all():
                if actual.value is not None:
                    actuals.append(actual.value)

        if len(actuals) != 0:
            return sum(actuals)
        return None
