from model_utils import Choices

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models

from greenbudget.app.actual.models import Actual
from greenbudget.app.budget_item.models import BudgetItem
from greenbudget.app.comment.models import Comment
from greenbudget.app.history.models import Event


class SubAccount(BudgetItem):
    type = "subaccount"
    name = models.CharField(max_length=128, null=True)
    quantity = models.IntegerField(null=True)
    rate = models.DecimalField(decimal_places=2, max_digits=10, null=True)
    multiplier = models.IntegerField(null=True)
    UNITS = Choices(
        (0, "minutes", "Minutes"),
        (1, "hours", "Hours"),
        (2, "weeks", "Weeks"),
        (3, "months", "Months"),
        (4, "days", "Days"),
        (5, "nights", "Nights"),
    )
    unit = models.IntegerField(choices=UNITS, null=True)

    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='account')
        | models.Q(app_label='subaccount', model='subaccount')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')
    subaccounts = GenericRelation('self')
    actuals = GenericRelation(Actual)
    comments = GenericRelation(Comment)
    events = GenericRelation(Event)

    DERIVING_FIELDS = [
        "name",
        "quantity",
        "rate",
        "multiplier",
        "unit"
    ]

    class Meta:
        get_latest_by = "updated_at"
        # Since the data from this model is used to power AGGridReact tables,
        # we want to keep the ordering of the accounts consistent.
        ordering = ('created_at', )
        verbose_name = "Sub Account"
        verbose_name_plural = "Sub Accounts"

    def __str__(self):
        return "<{cls} id={id}, name={name}, line={line}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            name=self.name,
            line=self.line,
        )

    @property
    def estimated(self):
        if self.subaccounts.count() == 0:
            if self.quantity is not None and self.rate is not None:
                multiplier = self.multiplier or 1.0
                return float(self.quantity) * float(self.rate) * float(multiplier)  # noqa
            return None
        else:
            estimated = []
            for subaccount in self.subaccounts.all():
                if subaccount.estimated is not None:
                    estimated.append(subaccount.estimated)
            if len(estimated) != 0:
                return sum(estimated)
            return None

    @property
    def unit_name(self):
        if self.unit is None:
            return ""
        return self.UNITS[self.unit]

    @property
    def account(self):
        from greenbudget.app.account.models import Account
        # TODO: We need to figure out a way to build this validation into the
        # model so that it does not accidentally happen.  There should always
        # be a top level SubAccount that has an Account as a parent.
        parent = self.parent
        while not isinstance(parent, Account):
            parent = parent.parent
        return parent

    @property
    def ancestors(self):
        return self.parent.ancestors + [self.parent]

    @property
    def parent_type(self):
        if isinstance(self.parent, self.__class__):
            return "subaccount"
        return "account"
