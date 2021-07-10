from model_utils import Choices
from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from greenbudget.app import signals
from greenbudget.app.comment.models import Comment

from .duplication import BudgetDuplicator
from .managers import BudgetManager, BaseBudgetManager


def upload_to(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{instance.type}_image_{instance.pk}.{ext}"
    return f'users/{instance.created_by.email.lower()}/{instance.type}s/{filename}'  # noqa


class BaseBudget(PolymorphicModel):
    name = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='budgets',
        on_delete=models.CASCADE
    )
    estimated = models.FloatField(default=0.0)
    image = models.ImageField(upload_to=upload_to, null=True)

    objects = BaseBudgetManager()
    non_polymorphic = models.Manager()

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('-updated_at', )
        verbose_name = "Base Budget"
        verbose_name_plural = "Base Budgets"

    def __str__(self):
        return "<{cls} id={id}, name={name}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            name=self.name
        )

    def duplicate(self, user):
        duplicator = BudgetDuplicator(self, user)
        return duplicator.duplicate()


@signals.model(flags='suppress_budget_update')
class Budget(BaseBudget):
    type = "budget"
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
    actual = models.FloatField(default=0.0)

    comments = GenericRelation(Comment)

    objects = BudgetManager()
    non_polymorphic = models.Manager()

    FIELDS_TO_DERIVE = ()
    FIELDS_TO_DUPLICATE = (
        'project_number', 'production_type', 'shoot_date', 'delivery_date',
        'build_days', 'prelight_days', 'studio_shoot_days', 'location_days',
        'image', 'name', 'actual', 'estimated'
    )

    class Meta(BaseBudget.Meta):
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"

    @property
    def variance(self):
        return float(self.estimated) - float(self.actual)
