from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from greenbudget.lib.model_tracker import track_model

from greenbudget.app.actual.models import Actual
from greenbudget.app.budget_item.models import BudgetItem, BudgetItemGroup
from greenbudget.app.budget_item.hooks import (
    on_create, on_field_change, on_group_removal)
from greenbudget.app.comment.models import Comment
from greenbudget.app.history.models import Event
from greenbudget.app.subaccount.models import SubAccount, SubAccountGroup


# Right now, we still need to iron out a discrepancy in the UI: whether or not
# the actuals for parent line items should be determined from the sum of the
# actuals of it's children, or the sum of the actuals tied to the parent.  This
# is a temporary toggle to switch between the two.
DETERMINE_ACTUAL_FROM_UNDERLYINGS = True


class AccountGroup(BudgetItemGroup):
    name = models.CharField(max_length=128)
    budget = models.ForeignKey(
        to='budget.Budget',
        related_name="groups",
        on_delete=models.CASCADE,
        db_index=True,
    )

    class Meta:
        get_latest_by = "created_at"
        ordering = ('created_at', )
        verbose_name = "Account Group"
        verbose_name_plural = "Account Groups"
        unique_together = (('budget', 'name'))


@track_model(
    on_create=on_create,
    # track_removal_of_fields=['group'],
    user_field='updated_by',
    # on_field_removal_hooks={'group': on_group_removal},
    on_field_change=on_field_change,
    track_changes_to_fields=['description', 'identifier'],
)
class Account(BudgetItem):
    type = "account"
    access = models.ManyToManyField(
        to='user.User',
        related_name='accessible_accounts'
    )
    subaccounts = GenericRelation(SubAccount)
    actuals = GenericRelation(Actual)
    comments = GenericRelation(Comment)
    events = GenericRelation(Event)
    groups = GenericRelation(SubAccountGroup)

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
    def estimated(self):
        estimated = []
        for subaccount in self.subaccounts.all():
            if subaccount.estimated is not None:
                estimated.append(subaccount.estimated)
        if len(estimated) != 0:
            return sum(estimated)
        return None
