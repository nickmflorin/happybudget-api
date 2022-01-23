from model_utils import Choices

from django.db import models

from greenbudget.app import signals
from greenbudget.app.budgeting.models import BudgetingRowModel

from .managers import FringeManager, BudgetFringeManager, TemplateFringeManager


@signals.model(user_field='updated_by')
class Fringe(BudgetingRowModel):
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

    type = "fringe"
    table_pivot = ('budget_id', )

    class Meta:
        get_latest_by = "order"
        ordering = ('order', )
        verbose_name = "Fringe"
        verbose_name_plural = "Fringes"
        unique_together = (('budget', 'order'))

    def __str__(self):
        return "<{cls} name={name}>".format(
            cls=self.__class__.__name__,
            name=self.name
        )

    def validate_before_save(self, bulk_context=False):
        super().validate_before_save(bulk_context=bulk_context)
        # In the case that the Fringe is added with a flat value, the cutoff
        # is irrelevant.
        if self.unit == self.UNITS.flat:
            self.cutoff = None

    @property
    def unit_name(self):
        if self.unit is None:
            return ""
        return self.UNITS[self.unit]


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
