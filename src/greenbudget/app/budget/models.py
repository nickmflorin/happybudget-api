import datetime
import functools
import logging
from model_utils import Choices

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from greenbudget.app import signals
from greenbudget.app.budgeting.models import BudgetingPolymorphicModel
from greenbudget.app.group.models import Group
from greenbudget.app.markup.models import Markup
from greenbudget.app.io.utils import upload_user_image_to

from .cache import (
    budget_markups_cache,
    budget_detail_cache,
    budget_accounts_cache,
    budget_groups_cache,
    budget_fringes_cache,
    budget_actuals_cache
)
from .duplication import BudgetDuplicator
from .managers import BudgetManager, BaseBudgetManager


logger = logging.getLogger('greenbudget')


def upload_to(instance, filename):
    return upload_user_image_to(
        user=instance.created_by,
        filename=filename,
        directory="budgets"
    )


ESTIMATED_FIELDS = (
    'accumulated_value',
    'accumulated_markup_contribution',
    'accumulated_fringe_contribution'
)
CALCULATED_FIELDS = ESTIMATED_FIELDS + ('actual', )


class BaseBudget(BudgetingPolymorphicModel):
    name = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='budgets',
        on_delete=models.CASCADE,
        editable=False
    )
    image = models.ImageField(upload_to=upload_to, null=True)

    ESTIMATED_FIELDS = ESTIMATED_FIELDS
    CALCULATED_FIELDS = CALCULATED_FIELDS

    actual = models.FloatField(default=0.0)
    accumulated_value = models.FloatField(default=0.0)
    accumulated_fringe_contribution = models.FloatField(default=0.0)
    accumulated_markup_contribution = models.FloatField(default=0.0)

    groups = GenericRelation(Group)
    children_markups = GenericRelation(Markup)

    FIELDS_TO_DERIVE = ()
    FIELDS_TO_DUPLICATE = ('image', 'name') + CALCULATED_FIELDS

    objects = BaseBudgetManager()
    non_polymorphic = models.Manager()

    CACHES = [
        budget_detail_cache,
        budget_markups_cache,
        budget_groups_cache,
        budget_fringes_cache,
        budget_actuals_cache,
        budget_accounts_cache
    ]

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('-updated_at', )
        verbose_name = "Base Budget"
        verbose_name_plural = "Base Budgets"

    def __str__(self):
        return "Budget: %s" % self.name

    def duplicate(self, user):
        duplicator = BudgetDuplicator(self, user)
        return duplicator.duplicate()

    @property
    def nominal_value(self):
        return self.accumulated_value

    @property
    def realized_value(self):
        return self.nominal_value + self.accumulated_fringe_contribution \
            + self.accumulated_markup_contribution

    def mark_updated(self):
        logger.debug(
            "Marking Budget %s Updated at %s"
            % (self.pk, datetime.datetime.now())
        )
        self.save(update_fields=['updated_at'])

    def accumulate_value(self, children=None):
        children = children or self.children.all()
        previous_value = self.accumulated_value
        self.accumulated_value = functools.reduce(
            lambda current, account: current + account.nominal_value,
            children,
            0
        )
        return previous_value != self.accumulated_value

    def accumulate_markup_contribution(self, children=None, to_be_deleted=None):
        children = children or self.children.all()
        markups = self.children_markups.filter(
            unit=Markup.UNITS.flat).exclude(pk__in=to_be_deleted or [])

        previous_value = self.accumulated_markup_contribution
        self.accumulated_markup_contribution = functools.reduce(
            lambda current, account: current + account.markup_contribution
            + account.accumulated_markup_contribution,
            children,
            0
        ) + functools.reduce(
            lambda current, markup: current + markup.rate,
            markups,
            0
        )
        return self.accumulated_markup_contribution != previous_value

    def accumulate_fringe_contribution(self, children=None):
        children = children or self.children.all()
        previous_value = self.accumulated_fringe_contribution
        self.accumulated_fringe_contribution = functools.reduce(
            lambda current, account: current
            + account.accumulated_fringe_contribution,
            children,
            0
        )
        return self.accumulated_fringe_contribution != previous_value

    def estimate(self, **kwargs):
        children, kwargs = self.children_from_kwargs(**kwargs)

        alterations = [
            self.accumulate_value(children=children),
            self.accumulate_fringe_contribution(children=children),
            self.accumulate_markup_contribution(
                children=children,
                to_be_deleted=kwargs.get('markups_to_be_deleted', [])
            )
        ]
        if any(alterations) and kwargs.get('commit', False):
            logger.debug(
                "Updating %s %s -> Accumulated Value: %s"
                % (type(self).__name__, self.pk, self.accumulated_value)
            )
            self.save(update_fields=self.reestimated_fields)
        return any(alterations)

    def calculate(self, **kwargs):
        return self.estimate(**kwargs)


@signals.model()
class Budget(BaseBudget):
    type = "budget"
    pdf_type = "pdf-budget"

    project_number = models.IntegerField(default=0)
    PRODUCTION_TYPES = Choices(
        (0, "film", "Film"),
        (1, "episodic", "Episodic"),
        (2, "music_video", "Music Video"),
        (3, "commercial", "Commercial"),
        (4, "documentary", "Documentary"),
        (5, "custom", "Custom"),
    )
    production_type = models.IntegerField(
        choices=PRODUCTION_TYPES,
        default=PRODUCTION_TYPES.film
    )
    shoot_date = models.DateTimeField(default=timezone.now)
    delivery_date = models.DateTimeField(default=timezone.now)
    build_days = models.IntegerField(default=0)
    prelight_days = models.IntegerField(default=0)
    studio_shoot_days = models.IntegerField(default=0)
    location_days = models.IntegerField(default=0)

    objects = BudgetManager()
    non_polymorphic = models.Manager()

    FIELDS_TO_DUPLICATE = BaseBudget.FIELDS_TO_DUPLICATE + (
        'project_number', 'production_type', 'shoot_date', 'delivery_date',
        'build_days', 'prelight_days', 'studio_shoot_days', 'location_days'
    )

    class Meta(BaseBudget.Meta):
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"

    @property
    def child_instance_cls(self):
        from greenbudget.app.account.models import BudgetAccount
        return BudgetAccount

    def actualize(self, **kwargs):
        children, kwargs = self.children_from_kwargs(**kwargs)
        markups_to_be_deleted = kwargs.get('markups_to_be_deleted', []) or []

        previous_value = self.actual
        self.actual = functools.reduce(
            lambda current, markup: current + (markup.actual or 0),
            self.children_markups.exclude(pk__in=markups_to_be_deleted),
            0
        ) + functools.reduce(
            lambda current, child: current + (child.actual or 0),
            children,
            0
        )
        if previous_value != self.actual and kwargs.get('commit', False):
            logger.debug(
                "Updating %s %s -> Actual: %s"
                % (type(self).__name__, self.pk, self.actual)
            )
            self.save(update_fields=['actual'])
        return previous_value != self.actual

    def calculate(self, **kwargs):
        children, kwargs = self.children_from_kwargs(**kwargs)
        commit = kwargs.pop('commit', False)
        alterations = [
            super().calculate(
                children=children,
                trickle=False,
                commit=False,
                **kwargs
            ),
            self.actualize(
                children=children,
                trickle=False,
                commit=False,
                **kwargs
            )
        ]
        if any(alterations) and commit:
            self.save(
                update_fields=tuple(self.reestimated_fields) + ('actual', ))
        return any(alterations)
