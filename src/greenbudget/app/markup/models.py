import functools
import logging
from model_utils import Choices

from django.db import models
from django.contrib.contenttypes.fields import (
    GenericRelation, GenericForeignKey)
from django.contrib.contenttypes.models import ContentType

from greenbudget.app import signals
from greenbudget.app.actual.models import Actual
from greenbudget.app.budgeting.models import BudgetingModel

from .managers import MarkupManager


logger = logging.getLogger('greenbudget')


@signals.model(user_field='updated_by')
class Markup(BudgetingModel):
    type = "markup"
    identifier = models.CharField(null=True, max_length=128)
    description = models.CharField(null=True, max_length=128)
    UNITS = Choices(
        (0, "percent", "Percent"),
        (1, "flat", "Flat"),
    )
    unit = models.IntegerField(choices=UNITS, default=UNITS.percent, null=False)
    rate = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_markups',
        on_delete=models.CASCADE,
        editable=False
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_markups',
        on_delete=models.CASCADE,
        editable=False
    )
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='account', model='account')
        | models.Q(app_label='subaccount', model='subaccount')
        | models.Q(app_label='budget', model='basebudget')
    )
    object_id = models.PositiveIntegerField(db_index=True)
    parent = GenericForeignKey('content_type', 'object_id')

    actuals = GenericRelation(Actual)
    objects = MarkupManager()

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('created_at', )
        verbose_name = "Markup"
        verbose_name_plural = "Markups"

    def __str__(self):
        return "Markup: %s" % self.identifier

    @property
    def actual(self):
        return functools.reduce(
            lambda current, actual: current + (actual.value or 0),
            self.actuals.only('value'),
            0
        )

    @property
    def child_instance_cls(self):
        return self.parent.child_instance_cls

    @property
    def parent_instance_cls(self):
        return type(self.parent)

    @property
    def children(self):
        return self.child_instance_cls.objects.filter(markups=self)

    def get_children_operator(self):
        if self.parent_instance_cls.type in ('account', 'subaccount'):
            return self.subaccounts
        return self.accounts

    def set_children(self, *children):
        operator = self.get_children_operator()
        operator.set(*children)

    def clear_children(self):
        operator = self.get_children_operator()
        operator.set([])

    def remove_children(self, *children):
        operator = self.get_children_operator()
        operator.remove(*children)

    def add_children(self, *children):
        operator = self.get_children_operator()
        operator.add(*children)

    @property
    def budget(self):
        parent = self.parent
        while not isinstance(parent, self.budget_cls):
            parent = parent.parent
        return parent

    @property
    def is_empty(self):
        # If there are Group(s) that are marked up but the Markup itself does
        # not have any SubAccount(s) or Account(s), then the Group will be
        # empty.
        return self.children.count() == 0
