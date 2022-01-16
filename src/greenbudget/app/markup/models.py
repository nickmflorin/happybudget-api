import functools
import logging
from model_utils import Choices

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.contenttypes.fields import (
    GenericRelation, GenericForeignKey)
from django.contrib.contenttypes.models import ContentType

from greenbudget.lib.django_utils.models import generic_fk_instance_change

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

    @property
    def intermittent_parent(self):
        try:
            self.parent.refresh_from_db()
        except (ObjectDoesNotExist, AttributeError):
            return None
        return self.parent

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
    def intermittent_budget(self):
        parent = self.intermittent_parent
        while not isinstance(parent, self.budget_cls):
            if parent is None:
                break
            parent = parent.intermittent_parent
        return parent

    @property
    def is_empty(self):
        # If there are Group(s) that are marked up but the Markup itself does
        # not have any SubAccount(s) or Account(s), then the Group will be
        # empty.
        return self.children.count() == 0

    def get_children_to_reestimate(self):
        """
        If :obj:`Markup` has a non-null value for `rate`, then the
        :obj:`Markup`'s will have a contribution to the estimated values of it's
        children, whether the children be instances of :obj:`Account` or
        :obj:SubAccount`, has changed.

        This means that when a :obj:`Markup` is just created or it's values for
        `rate` and/or `unit` have changed, it's children have to be reestimated.

        This method looks at an instance of :obj:`Markup` and returns the
        children that need to be reestimated as a result of a change to the
        :obj:`Markup` or the creation of the :obj:`Markup`.
        """
        # If the Markup is in the midst of being created, we always want
        # to estimate the children.
        if self._state.adding is True or self.was_just_added() \
                or self.fields_have_changed('unit', 'rate'):
            return set(
                list(self.accounts.all()) + list(self.subaccounts.all()))
        return set()

    def get_parents_to_reestimate(self):
        """
        If :obj:`Markup` has a non-null value for `rate`, that :obj:`Markup`
        will have a contribution to the estimated values of it's parent, whether
        that parent be a :obj:`BaseBudget`, :obj:`Account` or :obj:`SubAccount`.

        This means that whenever a :obj:`Markup` is added, it's parent is
        changed or it's `unit` or `rate` fields have changed, the parent needs
        to be reestimated.  In the case that the parent has changed, both the
        new and old parent need to be reesetimated.

        This method looks at an instance of :obj:`Markup` and returns the parent
        or parents (in the case that the parent has changed) that need to be
        reestimated as a result of a change to the :obj:`Markup` or the
        creation of the :obj:`Markup`.
        """
        parents_to_reestimate = set([])
        # If the Markup is in the midst of being created, we always want
        # to estimate the parent.
        if self._state.adding is True or self.was_just_added():
            if self.parent is not None:
                parents_to_reestimate.add(self.parent)
        else:
            # We only need to reestimate the parent if the parent was changed
            # or the markup unit or rate was changed.
            old_parent, new_parent = generic_fk_instance_change(self)
            if old_parent != new_parent:
                parents_to_reestimate.update([
                    x for x in [old_parent, new_parent]
                    if x is not None
                ])
            elif self.fields_have_changed('unit', 'rate') \
                    and self.parent is not None:
                parents_to_reestimate.add(self.parent)
        return parents_to_reestimate
