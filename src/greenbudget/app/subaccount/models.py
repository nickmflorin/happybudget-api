from model_utils import Choices

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models


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
    multiplier = models.DecimalField(decimal_places=2, max_digits=10, null=True)
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
    content_object = GenericForeignKey('content_type', 'object_id')
    subaccounts = GenericRelation('self')

    DERIVING_FIELDS = [
        "quantity",
        "rate",
        "multiplier",
        "unit"
    ]

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
                return self.quantity * self.rate
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
        parent = self.content_object
        while not isinstance(parent, Account):
            parent = parent.content_object
        return parent

    @property
    def variance(self):
        return None

    @property
    def ancestors(self):
        return self.content_object.ancestors + [self.content_object]
