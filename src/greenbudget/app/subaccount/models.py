from polymorphic.models import PolymorphicModel
from model_utils import Choices

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError

from greenbudget.lib.model_tracker import track_model

from greenbudget.app.actual.models import Actual
from greenbudget.app.comment.models import Comment
from greenbudget.app.fringe.utils import fringe_value
from greenbudget.app.group.hooks import on_group_removal
from greenbudget.app.group.models import (
    BudgetSubAccountGroup, TemplateSubAccountGroup)
from greenbudget.app.history.models import Event
from greenbudget.app.history.hooks import on_create, on_field_change

from .managers import SubAccountManager, BudgetSubAccountManager

# Right now, we still need to iron out a discrepancy in the UI: whether or not
# the actuals for parent line items should be determined from the sum of the
# actuals of it's children, or the sum of the actuals tied to the parent.  This
# is a temporary toggle to switch between the two.
DETERMINE_ACTUAL_FROM_UNDERLYINGS = False


class SubAccount(PolymorphicModel):
    type = "subaccount"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    identifier = models.CharField(max_length=128)
    description = models.CharField(null=True, max_length=128)
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
        (6, "allow", "Allow"),
        (7, "flat", "Flat"),
        (8, "feet", "Feet"),
        (9, "fare", "Fare"),
        (10, "units", "Units"),
    )
    unit = models.IntegerField(choices=UNITS, null=True)
    fringes = models.ManyToManyField(to='fringe.Fringe')
    budget = models.ForeignKey(
        to='budget.BaseBudget',
        on_delete=models.CASCADE,
        related_name='subaccounts'
    )
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='Account')
        | models.Q(app_label='subaccount', model='SubAccount')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')
    subaccounts = GenericRelation('self')
    objects = SubAccountManager()

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
        unique_together = (('content_type', 'object_id', 'identifier'), )

    def __str__(self):
        return "<{cls} id={id}, name={name}, identifier={identifier}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            name=self.name,
            identifier=self.identifier,
        )

    @property
    def siblings(self):
        return [
            subaccount for subaccount in self.parent.subaccounts.all()
            if subaccount != self
        ]

    @property
    def ancestors(self):
        return self.parent.ancestors + [self.parent]

    @property
    def parent_type(self):
        # TODO: THIS PROBABLY WONT WORK ANYMORE
        if isinstance(self.parent, self.__class__):
            return "subaccount"
        return "account"

    @property
    def estimated(self):
        if self.subaccounts.count() == 0:
            if self.quantity is not None and self.rate is not None:
                multiplier = self.multiplier or 1.0
                value = float(self.quantity) * float(self.rate) * float(multiplier)  # noqa
                return fringe_value(value, self.fringes.all())
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
    def account(self):
        from greenbudget.app.account.models import Account
        parent = self.parent
        while not isinstance(parent, Account):
            parent = parent.parent
        return parent

    def save(self, *args, **kwargs):
        if self.group is not None and self.group.parent != self.parent:
            raise IntegrityError(
                "The group that an item belongs to must have the same parent "
                "as that item."
            )
        if self.id is not None:
            for fringe in self.fringes.all():
                if fringe.budget != self.budget:
                    raise IntegrityError(
                        "The fringes that belong to a sub-account must belong "
                        "to the same budget as that sub-account."
                    )
        return super().save(*args, **kwargs)


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
class BudgetSubAccount(SubAccount):
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_budget_subaccounts',
        on_delete=models.SET_NULL,
        null=True
    )
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_budget_subaccounts',
        on_delete=models.SET_NULL,
        null=True
    )
    group = models.ForeignKey(
        to='group.BudgetSubAccountGroup',
        null=True,
        on_delete=models.SET_NULL,
        related_name='children'
    )
    actuals = GenericRelation(Actual)
    comments = GenericRelation(Comment)
    events = GenericRelation(Event)
    groups = GenericRelation(BudgetSubAccountGroup)
    objects = BudgetSubAccountManager()

    MAP_FIELDS_FROM_TEMPLATE = (
        'identifier', 'description', 'name', 'rate', 'quantity', 'multiplier',
        'unit')

    class Meta(SubAccount.Meta):
        verbose_name = "Budget Sub Account"
        verbose_name_plural = "Budget Sub Accounts"

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
class TemplateSubAccount(SubAccount):
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_template_subaccounts',
        on_delete=models.SET_NULL,
        null=True
    )
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_template_subaccounts',
        on_delete=models.SET_NULL,
        null=True
    )
    group = models.ForeignKey(
        to='group.TemplateSubAccountGroup',
        null=True,
        on_delete=models.SET_NULL,
        related_name='children'
    )
    groups = GenericRelation(TemplateSubAccountGroup)

    class Meta(SubAccount.Meta):
        verbose_name = "Template Sub Account"
        verbose_name_plural = "Template Sub Accounts"
