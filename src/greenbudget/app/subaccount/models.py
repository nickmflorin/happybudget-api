from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError
from django.db.models.signals import m2m_changed

from greenbudget.app import signals

from greenbudget.app.comment.models import Comment
from greenbudget.app.group.models import (
    BudgetSubAccountGroup, TemplateSubAccountGroup)
from greenbudget.app.history.models import Event
from greenbudget.app.tagging.models import Tag

from .managers import (
    SubAccountManager, BudgetSubAccountManager, TemplateSubAccountManager)


class SubAccountUnit(Tag):
    color = models.ForeignKey(
        to="tagging.Color",
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to=models.Q(
            content_types__model="subaccountunit",
            content_types__app_label="subaccount"
        ))

    class Meta:
        get_latest_by = "created_at"
        ordering = ("order",)
        verbose_name = "Sub Account Unit"
        verbose_name_plural = "Sub Account Units"

    def __str__(self):
        color_string = None if self.color is None else self.color.code
        return "<{cls} id={id}, color={color}, title={title}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            color=color_string,
            title=self.title
        )


@signals.model('suppress_budget_update')
class SubAccount(PolymorphicModel):
    type = "subaccount"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    identifier = models.CharField(null=True, max_length=128)
    description = models.CharField(null=True, max_length=128)
    name = models.CharField(max_length=128, null=True)
    quantity = models.IntegerField(null=True)
    rate = models.FloatField(null=True)
    multiplier = models.IntegerField(null=True)
    estimated = models.FloatField(default=0.0)
    unit = models.ForeignKey(
        to='subaccount.SubAccountUnit',
        on_delete=models.SET_NULL,
        null=True
    )
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
    def account(self):
        from greenbudget.app.account.models import Account
        parent = self.parent
        while not isinstance(parent, Account):
            parent = parent.parent
        return parent

    def save(self, *args, **kwargs):
        # TODO: For whatever reason, this validation does not seem to work when
        # updating a specific Group with { children: [] } via the API.  The
        # group is always None.
        if self.group is not None and self.group.parent != self.parent:
            raise IntegrityError(
                "The group that an item belongs to must have the same parent "
                "as that item."
            )
        return super().save(*args, **kwargs)


def validate_fringes(sender, **kwargs):
    from greenbudget.app.fringe.models import Fringe
    if kwargs['action'] == 'pre_add' and kwargs['model'] == Fringe:
        fringes = (Fringe.objects
            .filter(pk__in=kwargs['pk_set'])
            .prefetch_related('budget')
            .only('budget')
            .all())
        for fringe in fringes:
            if fringe.budget != kwargs['instance'].budget:
                raise IntegrityError(
                    "The fringes that belong to a sub-account must belong "
                    "to the same budget as that sub-account."
                )


m2m_changed.connect(validate_fringes, sender=SubAccount.fringes.through)


@signals.track_model(
    user_field='updated_by',
    track_changes_to_fields=[
        'description', 'identifier', 'name', 'rate', 'quantity', 'multiplier',
        'object_id', 'group'],
)
@signals.model('track_changes')
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
    actual = models.FloatField(default=0.0)

    comments = GenericRelation(Comment)
    events = GenericRelation(Event)
    groups = GenericRelation(BudgetSubAccountGroup)
    objects = BudgetSubAccountManager()

    MAP_FIELDS_FROM_TEMPLATE = (
        'identifier', 'description', 'name', 'rate', 'quantity', 'multiplier',
        'unit')
    MAP_FIELDS_FROM_ORIGINAL = (
        'identifier', 'description', 'name', 'rate', 'quantity', 'multiplier',
        'unit')
    TRACK_MODEL_HISTORY = True

    class Meta(SubAccount.Meta):
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
    def variance(self):
        return float(self.estimated) - float(self.actual)


@signals.track_model(
    user_field='updated_by',
    track_changes_to_fields=['group', 'rate', 'quantity', 'multiplier'],
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
    objects = TemplateSubAccountManager()
    MAP_FIELDS_FROM_ORIGINAL = (
        'identifier', 'description', 'name', 'rate', 'quantity', 'multiplier',
        'unit')

    class Meta(SubAccount.Meta):
        verbose_name = "Sub Account"
        verbose_name_plural = "Sub Accounts"

    def __str__(self):
        return "<{cls} id={id}, name={name}, identifier={identifier}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            name=self.name,
            identifier=self.identifier,
        )
