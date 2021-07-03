from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, IntegrityError

from greenbudget.app import signals

from greenbudget.app.comment.models import Comment
from greenbudget.app.group.models import (
    BudgetSubAccountGroup, TemplateSubAccountGroup)
from greenbudget.app.history.models import Event
from greenbudget.app.subaccount.models import SubAccount

from .managers import AccountManager


class Account(PolymorphicModel):
    type = "account"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    identifier = models.CharField(null=True, max_length=128)
    description = models.CharField(null=True, max_length=128)
    budget = models.ForeignKey(
        to='budget.BaseBudget',
        on_delete=models.CASCADE,
        related_name='accounts'
    )
    estimated = models.FloatField(default=0.0)
    subaccounts = GenericRelation(SubAccount)

    objects = AccountManager()
    non_polymorphic = models.Manager()

    class Meta:
        get_latest_by = "updated_at"
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
    def siblings(self):
        return [
            account for account in self.budget.accounts.all()
            if account != self
        ]

    def save(self, *args, **kwargs):
        if self.group is not None and self.group.parent != self.budget:
            raise IntegrityError(
                "The group that an account belongs to must belong to the same "
                "budget as that account."
            )
        return super().save(*args, **kwargs)


@signals.model(
    flags=['suppress_budget_update'],
    user_field='updated_by',
    exclude_fields=['updated_by', 'created_by', 'estimated', 'actual']
)
class BudgetAccount(Account):
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_budget_accounts',
        on_delete=models.SET_NULL,
        null=True
    )
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_budget_accounts',
        on_delete=models.SET_NULL,
        null=True
    )
    access = models.ManyToManyField(
        to='user.User',
        related_name='accessible_accounts'
    )
    group = models.ForeignKey(
        to='group.BudgetAccountGroup',
        null=True,
        on_delete=models.SET_NULL,
        related_name='children'
    )
    actual = models.FloatField(default=0.0)

    comments = GenericRelation(Comment)
    events = GenericRelation(Event)
    groups = GenericRelation(BudgetSubAccountGroup)

    FIELDS_TO_DUPLICATE = (
        'identifier', 'description', 'actual', 'estimated')
    TRACK_MODEL_HISTORY = True
    TRACK_FIELD_CHANGE_HISTORY = ['identifier', 'description']

    objects = AccountManager()

    class Meta(Account.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    @property
    def variance(self):
        return float(self.estimated) - float(self.actual)


@signals.model(
    flags=['suppress_budget_update'],
    user_field='updated_by',
    exclude_fields=['updated_by', 'created_by', 'estimated']
)
class TemplateAccount(Account):
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_template_accounts',
        on_delete=models.SET_NULL,
        null=True
    )
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_template_accounts',
        on_delete=models.SET_NULL,
        null=True
    )
    group = models.ForeignKey(
        to='group.TemplateAccountGroup',
        null=True,
        on_delete=models.SET_NULL,
        related_name='children'
    )
    groups = GenericRelation(TemplateSubAccountGroup)

    objects = AccountManager()

    FIELDS_TO_DUPLICATE = ('identifier', 'description', 'estimated')
    FIELDS_TO_DERIVE = ('identifier', 'description', 'estimated')

    class Meta(Account.Meta):
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
