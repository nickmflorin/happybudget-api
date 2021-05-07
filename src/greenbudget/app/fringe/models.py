from model_utils import Choices

from django.db import models

from .managers import FringeManager


class Fringe(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(null=True, max_length=128)
    cutoff = models.FloatField(null=True)
    rate = models.FloatField(null=True)
    UNITS = Choices(
        (0, "percent", "Percent"),
        (1, "flat", "Flat"),
    )
    unit = models.IntegerField(choices=UNITS, default=UNITS.percent)
    budget = models.ForeignKey(
        to='budget.BaseBudget',
        on_delete=models.CASCADE,
        related_name='fringes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        to='user.User',
        related_name='created_fringes',
        on_delete=models.SET_NULL,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        to='user.User',
        related_name='updated_fringes',
        on_delete=models.SET_NULL,
        null=True
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
    MAP_FIELDS_FROM_ORIGINAL = ('name', 'description', 'cutoff', 'rate', 'unit')
    MAP_FIELDS_FROM_TEMPLATE = MAP_FIELDS_FROM_ORIGINAL
    objects = FringeManager()

    class Meta:
        get_latest_by = "updated_at"
        ordering = ('-created_at', )
        verbose_name = "Fringe"
        verbose_name_plural = "Fringes"
        unique_together = (('budget', 'name'), )

    @property
    def num_times_used(self):
        return 1  # Temporary - needs to be built in.

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
        setattr(self, '_suppress_budget_update',
            kwargs.pop('suppress_budget_update', False))
        super().save(*args, **kwargs)
