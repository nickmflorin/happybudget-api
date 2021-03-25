from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from greenbudget.app.actual.models import Actual
from greenbudget.app.budget_item.models import BudgetItem
from greenbudget.app.comment.models import Comment
from greenbudget.app.history.models import Event
from greenbudget.app.history.tracker import ModelHistoryTracker
from greenbudget.app.subaccount.models import SubAccount, SubAccountGroup


# Right now, we still need to iron out a discrepancy in the UI: whether or not
# the actuals for parent line items should be determined from the sum of the
# actuals of it's children, or the sum of the actuals tied to the parent.  This
# is a temporary toggle to switch between the two.
DETERMINE_ACTUAL_FROM_UNDERLYINGS = True


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
    subaccount_groups = GenericRelation(SubAccountGroup)

    field_history = ModelHistoryTracker(
        ['description', 'identifier'], user_field='updated_by')

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
    def estimated(self):
        estimated = []
        for subaccount in self.subaccounts.all():
            if subaccount.estimated is not None:
                estimated.append(subaccount.estimated)
        if len(estimated) != 0:
            return sum(estimated)
        return None
