from model_utils import Choices
from polymorphic.models import PolymorphicModel

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from greenbudget.app.comment.models import Comment

from .managers import BudgetManager, BaseBudgetManager
from .utils import render_budget_as_pdf


class BaseBudget(PolymorphicModel):
    name = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='budgets',
        on_delete=models.CASCADE
    )
    trash = models.BooleanField(default=False)
    objects = BaseBudgetManager()

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('-updated_at', )
        verbose_name = "Base Budget"
        verbose_name_plural = "Base Budgets"
        unique_together = (
            ('created_by', 'name', 'polymorphic_ctype_id', 'trash'),
        )

    def __str__(self):
        return "<{cls} id={id}, name={name}>".format(
            cls=self.__class__.__name__,
            id=self.pk,
            name=self.name
        )

    def to_trash(self):
        self.trash = True
        self.save()

    def restore(self):
        self.trash = False
        self.save()

    @property
    def estimated(self):
        estimated = []
        for account in self.accounts.all():
            if account.estimated is not None:
                estimated.append(account.estimated)
        if len(estimated) != 0:
            return sum(estimated)
        return None


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

    comments = GenericRelation(Comment)
    objects = BudgetManager()
    MAP_FIELDS_FROM_TEMPLATE = ()

    class Meta(BaseBudget.Meta):
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"

    @property
    def variance(self):
        if self.actual is not None and self.estimated is not None:
            return float(self.estimated) - float(self.actual)
        return None

    @property
    def actual(self):
        actuals = []
        for account in self.accounts.all():
            if account.actual is not None:
                actuals.append(account.actual)
        if len(actuals) != 0:
            return sum(actuals)
        return None

    def to_pdf(self):
        return render_budget_as_pdf(self)
