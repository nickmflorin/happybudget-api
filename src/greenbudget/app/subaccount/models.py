from model_utils import Choices

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models

from greenbudget.app.actual.models import Actual


class SubAccount(models.Model):
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
    description = models.CharField(null=True, max_length=128)
    name = models.CharField(max_length=128)
    line = models.CharField(max_length=128)
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
        limit_choices_to=models.Q(app_label='account', model='Account')
        | models.Q(app_label='subaccount', model='SubAccount')
    )
    object_id = models.PositiveIntegerField()
    parent = GenericForeignKey('content_type', 'object_id')
    subaccounts = GenericRelation('self')
    actuals = GenericRelation(Actual)

    DERIVING_FIELDS = [
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
        unique_together = (('object_id', 'content_type', 'name'), )

    def __str__(self):
        return "<{cls} id={id}, name={name}, line={line}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            name=self.name,
            line=self.line,
        )

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

    @property
    def estimated(self):
        if self.subaccounts.count() == 0:
            if self.quantity is not None and self.rate is not None:
                multiplier = self.multiplier or 1.0
                return self.quantity * self.rate * multiplier
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
    def variance(self):
        return None

    @property
    def ancestors(self):
        return self.parent.ancestors + [self.parent]
