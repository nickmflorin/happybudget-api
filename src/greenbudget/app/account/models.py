from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from greenbudget.app.actual.models import Actual
from greenbudget.app.budget_item.models import BudgetItem
from greenbudget.app.comment.models import Comment
from greenbudget.app.subaccount.models import SubAccount


class Account(BudgetItem):
    type = "account"
    access = models.ManyToManyField(
        to='user.User',
        related_name='accessible_accounts'
    )
    subaccounts = GenericRelation(SubAccount)
    actuals = GenericRelation(Actual)
    comments = GenericRelation(Comment)

    class Meta:
        get_latest_by = "updated_at"
        # Since the data from this model is used to power AGGridReact tables,
        # we want to keep the ordering of the accounts consistent.
        ordering = ('created_at', )
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    def __str__(self):
        return "<{cls} id={id}, identifier={identifier}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            identifier=self.identifier
        )

    @property
    def ancestors(self):
        return [self.budget]

    @property
    def variance(self):
        if self.actual is not None and self.estimated is not None:
            return float(self.estimated) - float(self.actual)
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

    @property
    def estimated(self):
        estimated = []
        for subaccount in self.subaccounts.all():
            if subaccount.estimated is not None:
                estimated.append(subaccount.estimated)
        if len(estimated) != 0:
            return sum(estimated)
        return None
