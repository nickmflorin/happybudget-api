from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, IntegrityError

from greenbudget.lib.model_tracker import track_model

from greenbudget.app.actual.models import Actual
from greenbudget.app.comment.models import Comment
from greenbudget.app.group.models import (
    BudgetSubAccountGroup, TemplateSubAccountGroup)
from greenbudget.app.group.hooks import on_group_removal
from greenbudget.app.history.models import Event
from greenbudget.app.history.hooks import on_create, on_field_change
from greenbudget.app.subaccount.models import SubAccount

from .managers import (
    AccountManager, BudgetAccountManager, TemplateAccountManager)

# Right now, we still need to iron out a discrepancy in the UI: whether or not
# the actuals for parent line items should be determined from the sum of the
# actuals of it's children, or the sum of the actuals tied to the parent.  This
# is a temporary toggle to switch between the two.
DETERMINE_ACTUAL_FROM_UNDERLYINGS = True


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
    subaccounts = GenericRelation(SubAccount)
    objects = AccountManager()

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

    @property
    def estimated(self):
        estimated = []
        for subaccount in self.subaccounts.all():
            if subaccount.estimated is not None:
                estimated.append(subaccount.estimated)
        if len(estimated) != 0:
            return sum(estimated)
        return None

    def save(self, *args, **kwargs):
        if self.group is not None and self.group.parent != self.budget:
            raise IntegrityError(
                "The group that an account belongs to must belong to the same "
                "budget as that account."
            )
        setattr(self, '_suppress_budget_update',
            kwargs.pop('suppress_budget_update', False))
        return super().save(*args, **kwargs)


@track_model(
    on_create=on_create,
    track_removal_of_fields=['group'],
    user_field='updated_by',
    on_field_removal_hooks={'group': on_group_removal},
    on_field_change=on_field_change,
    track_changes_to_fields=['description', 'identifier'],
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
    actuals = GenericRelation(Actual)
    comments = GenericRelation(Comment)
    events = GenericRelation(Event)
    groups = GenericRelation(BudgetSubAccountGroup)

    MAP_FIELDS_FROM_TEMPLATE = ('identifier', 'description')
    MAP_FIELDS_FROM_ORIGINAL = ('identifier', 'description')
    objects = BudgetAccountManager()

    class Meta(Account.Meta):
        verbose_name = "Budget Account"
        verbose_name_plural = "Budget Accounts"

    @property
    def variance(self):
        if self.actual is not None and self.estimated is not None:
            return float(self.estimated) - float(self.actual)
        return None

    @property
    def actual(self):
        actuals = []
        if DETERMINE_ACTUAL_FROM_UNDERLYINGS:
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


@track_model(
    track_removal_of_fields=['group'],
    on_field_removal_hooks={'group': on_group_removal},
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
    objects = TemplateAccountManager()
    MAP_FIELDS_FROM_ORIGINAL = ('identifier', 'description')

    class Meta(Account.Meta):
        verbose_name = "Template Account"
        verbose_name_plural = "Template Accounts"
