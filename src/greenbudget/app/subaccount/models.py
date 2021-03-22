from colorful.fields import RGBColorField
from model_utils import Choices

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError

from greenbudget.app.actual.models import Actual
from greenbudget.app.budget_item.models import BudgetItem
from greenbudget.app.comment.models import Comment
from greenbudget.app.history.models import Event
from greenbudget.app.history.tracker import ModelHistoryTracker


class SubAccountGroup(models.Model):
    name = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_sub_account_groups',
        on_delete=models.SET_NULL,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_sub_account_groups',
        on_delete=models.SET_NULL,
        null=True
    )
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='account')
        | models.Q(app_label='subaccount', model='subaccount')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')
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
        verbose_name = "Sub Account Group"
        verbose_name_plural = "Sub Account Groups"
        unique_together = (('object_id', 'content_type', 'name'))


class SubAccount(BudgetItem):
    type = "subaccount"
    name = models.CharField(max_length=128, null=True)
    quantity = models.IntegerField(null=True)
    rate = models.FloatField(null=True)
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
    group = models.ForeignKey(
        to='subaccount.SubAccountGroup',
        null=True,
        on_delete=models.SET_NULL,
        related_name='subaccounts'
    )

    subaccounts = GenericRelation('self')
    actuals = GenericRelation(Actual)
    comments = GenericRelation(Comment)
    events = GenericRelation(Event)
    subaccount_groups = GenericRelation(SubAccountGroup)

    field_history = ModelHistoryTracker(
        ['description', 'identifier', 'name', 'rate', 'quantity', 'multiplier',
        'unit'],
        user_field='updated_by'
    )

    DERIVING_FIELDS = [
        "name",
        "quantity",
        "rate",
        "multiplier",
        "unit"
    ]

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('created_at', )
        verbose_name = "Sub Account"
        verbose_name_plural = "Sub Accounts"

    def __str__(self):
        return "<{cls} id={id}, name={name}, identifier={identifier}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            name=self.name,
            identifier=self.identifier,
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

    def save(self, *args, **kwargs):
        if self.group is not None and self.group.parent != self.parent:
            raise IntegrityError(
                "The group that a subaccount belongs to must have the same "
                "parent as that subaccount."
            )
        return super().save(*args, **kwargs)
