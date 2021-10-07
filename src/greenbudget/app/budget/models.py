import functools
from model_utils import Choices
from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from greenbudget.lib.django_utils.models import optional_commit

from greenbudget.app import signals
from greenbudget.app.budgeting.models import use_children
from greenbudget.app.comment.models import Comment
from greenbudget.app.group.models import Group
from greenbudget.app.markup.models import Markup
from greenbudget.app.user.utils import upload_user_image_to

from .duplication import BudgetDuplicator
from .managers import BudgetManager, BaseBudgetManager


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


class BaseBudget(PolymorphicModel):
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

    groups = GenericRelation(Group)

    objects = BaseBudgetManager()
    non_polymorphic = models.Manager()

    ESTIMATED_FIELDS = ESTIMATED_FIELDS
    CALCULATED_FIELDS = CALCULATED_FIELDS

    actual = models.FloatField(default=0.0)
    accumulated_value = models.FloatField(default=0.0)
    accumulated_fringe_contribution = models.FloatField(default=0.0)
    accumulated_markup_contribution = models.FloatField(default=0.0)

    FIELDS_TO_DERIVE = ()
    FIELDS_TO_DUPLICATE = ('image', 'name') + CALCULATED_FIELDS

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

    @optional_commit(["accumulated_value"])
    @use_children(["nominal_value"])
    def accumulate_value(self, children, **kwargs):
        self.accumulated_value = functools.reduce(
            lambda current, account: current + account.nominal_value,
            children,
            0
        )

    @optional_commit(["accumulated_markup_contribution"])
    @use_children(["accumulated_markup_contribution", "markup_contribution"])
    def accumulate_markup_contribution(self, children, **kwargs):
        self.accumulated_markup_contribution = functools.reduce(
            lambda current, account: current + account.markup_contribution
            + account.accumulated_markup_contribution,
            children,
            0
        )

    @optional_commit(["accumulated_fringe_contribution"])
    @use_children(["accumulated_fringe_contribution", "fringe_contribution"])
    def accumulate_fringe_contribution(self, children, **kwargs):
        self.accumulated_fringe_contribution = functools.reduce(
            lambda current, account: current
            + account.accumulated_fringe_contribution,
            children,
            0
        )

    @optional_commit(["actual"])
    @use_children(["actual"])
    def actualize(self, children, **kwargs):
        self.actual = functools.reduce(
            lambda current, child: current + (child.actual or 0),
            children,
            0
        )

    @optional_commit(list(ESTIMATED_FIELDS))
    def estimate(self, **kwargs):
        children = self.children.only(*ESTIMATED_FIELDS) \
            .exclude(pk__in=kwargs.get('children_to_be_deleted') or []).all()
        self.accumulate_value(children=children, **kwargs)
        self.accumulate_fringe_contribution(children=children, **kwargs)
        self.accumulate_markup_contribution(children=children, **kwargs)


@signals.model(flags='suppress_budget_update')
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

    comments = GenericRelation(Comment)
    children_markups = GenericRelation(Markup)

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
