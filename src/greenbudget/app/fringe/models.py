from model_utils import Choices

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from greenbudget.app import signals
from greenbudget.app.tabling.models import BudgetingRowModel

from .managers import FringeManager, BudgetFringeManager, TemplateFringeManager


@signals.model(user_field='updated_by')
class Fringe(BudgetingRowModel):
    type = "fringe"
    name = models.CharField(max_length=128, null=True)
    description = models.CharField(null=True, max_length=128)
    cutoff = models.FloatField(null=True)
    rate = models.FloatField(null=True)
    UNITS = Choices(
        (0, "percent", "Percent"),
        (1, "flat", "Flat"),
    )
    unit = models.IntegerField(choices=UNITS, default=UNITS.percent, null=True)
    budget = models.ForeignKey(
        to='budget.BaseBudget',
        on_delete=models.CASCADE,
        related_name='fringes'
    )
    color = models.ForeignKey(
        to='tagging.Color',
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to=models.Q(
            content_types__model='fringe',
            content_types__app_label='fringe'
        )
    )
    objects = FringeManager()

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('created_at', )
        verbose_name = "Fringe"
        verbose_name_plural = "Fringes"

    def __str__(self):
        return "<{cls} name={name}>".format(
            cls=self.__class__.__name__,
            name=self.name
        )

    @property
    def unit_name(self):
        if self.unit is None:
            return ""
        return self.UNITS[self.unit]

    @property
    def intermittent_budget(self):
        try:
            self.budget.refresh_from_db()
        except (ObjectDoesNotExist, AttributeError):
            return None
        return self.budget


class BudgetFringe(Fringe):
    objects = BudgetFringeManager()

    class Meta:
        proxy = True
        verbose_name = "Fringe"
        verbose_name_plural = "Fringes"


class TemplateFringe(Fringe):
    objects = TemplateFringeManager()

    class Meta:
        proxy = True
        verbose_name = "Fringe"
        verbose_name_plural = "Fringes"
