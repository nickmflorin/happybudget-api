from model_utils import Choices

from django.db import models, IntegrityError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from greenbudget.app import signals

from .managers import MarkupManager


@signals.model(
    flags=['suppress_budget_update', 'suppress_markups_changed'],
    user_field='updated_by'
)
class Markup(models.Model):
    type = "markup"
    identifier = models.CharField(null=True, max_length=128)
    description = models.CharField(null=True, max_length=128)
    UNITS = Choices(
        (0, "percent", "Percent"),
        (1, "flat", "Flat"),
    )
    unit = models.IntegerField(choices=UNITS, default=UNITS.percent, null=True)
    rate = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_new_markups',
        on_delete=models.CASCADE,
        editable=False
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_new_markups',
        on_delete=models.CASCADE,
        editable=False
    )
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='budgetaccount')
        | models.Q(app_label='subaccount', model='budgetsubaccount')
        | models.Q(app_label='budget', model='budget')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')

    objects = MarkupManager()

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('-created_at', )
        verbose_name = "Markup"
        verbose_name_plural = "Markups"

    @classmethod
    def child_instance_cls_for_parent(cls, parent):
        from greenbudget.app.account.models import BudgetAccount
        from greenbudget.app.budget.models import Budget
        from greenbudget.app.subaccount.models import BudgetSubAccount

        mapping = {
            Budget: BudgetAccount,
            (BudgetAccount, BudgetSubAccount): BudgetSubAccount,
        }
        for k, v in mapping.items():
            if isinstance(parent, k):
                return v
        raise IntegrityError(
            "Unexpected instance %s - must be a valid parent of Group."
            % parent.__class__.__name__
        )

    @property
    def parent_instance_cls(self):
        return type(self.parent)

    @property
    def child_instance_cls(self):
        return self.child_instance_cls_for_parent(self.parent)

    @property
    def children(self):
        # Note that Groups are not included as children.
        return self.child_instance_cls.objects.filter(markups=self)

    def get_children_operator(self):
        from greenbudget.app.account.models import BudgetAccount
        from greenbudget.app.subaccount.models import BudgetSubAccount
        if self.parent_instance_cls is BudgetAccount \
                or self.parent_instance_cls is BudgetSubAccount:
            return self.subaccounts
        return self.accounts

    def set_children(self, *children):
        operator = self.get_children_operator()
        operator.set(*children)

    def remove_children(self, *children):
        operator = self.get_children_operator()
        operator.remove(*children)

    def add_children(self, *children):
        operator = self.get_children_operator()
        operator.add(*children)

    @property
    def budget(self):
        from greenbudget.app.budget.models import BaseBudget
        parent = self.parent
        while not isinstance(parent, BaseBudget):
            parent = parent.parent
        return parent

    @property
    def is_empty(self):
        # If there are Group(s) that are marked up but the Markup itself does
        # not have any SubAccount(s) or Account(s), then the Group will be
        # empty.
        return self.children.count() == 0

    def __str__(self):
        return "<{cls} identifier={identifier} parent={parent}>".format(
            cls=self.__class__.__name__,
            identifier=self.identifier,
            parent=self.parent.id,
        )
