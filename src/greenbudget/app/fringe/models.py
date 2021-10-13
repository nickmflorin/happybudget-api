from model_utils import Choices

from django.db import models

from greenbudget.app import signals

from .managers import FringeManager, BudgetFringeManager, TemplateFringeManager


@signals.model(
    flags='suppress_budget_update',
    user_field='updated_by'
)
class Fringe(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_fringes',
        on_delete=models.CASCADE,
        editable=False
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_fringes',
        on_delete=models.CASCADE,
        editable=False
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
    FIELDS_TO_DUPLICATE = (
        'name', 'description', 'cutoff', 'rate', 'unit', 'color')
    FIELDS_TO_DERIVE = FIELDS_TO_DUPLICATE
    objects = FringeManager()

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('-created_at', )
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

    def save(self, *args, **kwargs):
        # In the case that the Fringe is added with a flat value, the cutoff
        # is irrelevant.
        if self.unit == self.UNITS.flat:
            self.cutoff = None
        super().save(*args, **kwargs)


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
