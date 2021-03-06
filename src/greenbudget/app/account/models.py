from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from greenbudget.app.subaccount.models import SubAccount


class Account(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_accounts',
        on_delete=models.SET_NULL,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_accounts',
        on_delete=models.SET_NULL,
        null=True
    )
    account_number = models.CharField(max_length=128)
    description = models.CharField(null=True, max_length=128)
    access = models.ManyToManyField(
        to='user.User',
        related_name='accessible_accounts'
    )
    budget = models.ForeignKey(
        to='budget.Budget',
        related_name="accounts",
        on_delete=models.CASCADE
    )
    subaccounts = GenericRelation(SubAccount)

    class Meta:
        get_latest_by = "updated_at"
        # Since the data from this model is used to power AGGridReact tables,
        # we want to keep the ordering of the accounts consistent.
        ordering = ('-created_at', )
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        unique_together = (('account_number', 'budget'), )

    def __str__(self):
        return "<{cls} id={id}, account_number={account_number}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            account_number=self.account_number
        )

    @property
    def ancestors(self):
        return [self.budget]
