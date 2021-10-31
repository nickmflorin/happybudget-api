import functools
import logging
from model_utils import Choices

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.contenttypes.fields import (
    GenericRelation, GenericForeignKey)
from django.contrib.contenttypes.models import ContentType

from greenbudget.app import signals
from greenbudget.app.account.cache import account_markups_cache
from greenbudget.app.actual.models import Actual
from greenbudget.app.budget.cache import budget_markups_cache
from greenbudget.app.budgeting.utils import get_child_instance_cls
from greenbudget.app.subaccount.cache import subaccount_markups_cache

from .managers import MarkupManager


logger = logging.getLogger('greenbudget')


@signals.model(user_field='updated_by')
class Markup(models.Model):
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

    FIELDS_TO_DUPLICATE = ('identifier', 'description', 'unit', 'rate')
    FIELDS_TO_DERIVE = FIELDS_TO_DUPLICATE

    caches = {
        ('subaccount', ): subaccount_markups_cache,
        ('account', ): account_markups_cache,
        ('budget', 'template'): budget_markups_cache
    }

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('created_at', )
        verbose_name = "Markup"
        verbose_name_plural = "Markups"

    @property
    def actual(self):
        return functools.reduce(
            lambda current, actual: current + (actual.value or 0),
            self.actuals.only('value'),
            0
        )

    @classmethod
    def child_instance_cls_for_parent(cls, parent):
        return get_child_instance_cls(parent)

    @property
    def child_instance_cls(self):
        return self.child_instance_cls_for_parent(self.parent)

    @property
    def parent_instance_cls(self):
        return type(self.parent)

    @property
    def children(self):
        # Note that Groups are not included as children.
        return self.child_instance_cls.objects.filter(markups=self)

    @property
    def intermittent_parent(self):
        try:
            return self.parent
        except ObjectDoesNotExist:
            # The Account instance can be deleted in the process of deleting
            # it's parent, at which point the parent will be None or raise a
            # DoesNotExist Exception, until that Account instance is deleted.
            pass

    def invalidate_caches(self):
        parent = self.intermittent_parent
        if parent is None:
            logger.warn(
                "Cannot invalidate Markup caches because parent is not "
                "defined anymore."
            )
        else:
            for k, v in self.caches.items():
                if parent.type in k:
                    v.invalidate(parent)

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
        return "Markup: %s" % self.identifier
