from model_utils import Choices

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError

from greenbudget.lib.model_tracker import track_model

from greenbudget.app.actual.models import Actual
from greenbudget.app.budget_item.models import BudgetItem, BudgetItemGroup
from greenbudget.app.budget_item.hooks import (
    on_create, on_field_change, on_group_removal)
from greenbudget.app.comment.models import Comment
from greenbudget.app.history.models import Event


class SubAccountGroup(BudgetItemGroup):
    name = models.CharField(max_length=128)
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='account')
        | models.Q(app_label='subaccount', model='subaccount')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')

    class Meta:
        get_latest_by = "created_at"
        ordering = ('created_at', )
        verbose_name = "Sub Account Group"
        verbose_name_plural = "Sub Account Groups"
        unique_together = (('object_id', 'content_type', 'name'))


@track_model(
    on_create=on_create,
    track_removal_of_fields=['group'],
    user_field='updated_by',
    on_field_removal_hooks={'group': on_group_removal},
    on_field_change=on_field_change,
    track_changes_to_fields=[
        'description', 'identifier', 'name', 'rate', 'quantity', 'multiplier',
        'unit'],
)
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

    subaccounts = GenericRelation('self')
    actuals = GenericRelation(Actual)
    comments = GenericRelation(Comment)
    events = GenericRelation(Event)
    groups = GenericRelation(SubAccountGroup)

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
    def siblings(self):
        return self.parent.subaccounts.all()

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
