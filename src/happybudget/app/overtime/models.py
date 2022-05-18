from django.db import models

from happybudget.lib.django_utils.models import Choices
from happybudget.app.model import model
from happybudget.app.models import BaseModel


@model.model(type="overtime")
class Overtime(BaseModel(polymorphic=False)):
    budget = models.ForeignKey(
        to='budget.Budget',
        on_delete=models.CASCADE,
        related_name='overtimes'
    )
    OVERTIME_TYPES = Choices(
        (0, "time_and_half", "1.5x"),
        (1, "two_time", "2x"),
    )
    overtime_type = models.IntegerField(
        choices=OVERTIME_TYPES,
        default=OVERTIME_TYPES.time_and_half,
        null=False
    )
    start = models.FloatField(null=False, default=0.0)
    end = models.FloatField(null=True)

    class Meta:
        get_latest_by = "created_at"
        ordering = ('created_at', )
        verbose_name = "Overtime"
        verbose_name_plural = "Overtimes"
        unique_together = (('budget', 'overtime_type'))

    def __str__(self):
        if self.budget is not None and self.pk is not None:
            return f"Budget {self.budget.pk} Overtime {self.pk}"
        elif self.budget is not None:
            return f"Budget {self.budget.pk} Overtime ---"
        return "Budget --- Overtime ---"

    def overlaps(self, other):
        assert other.overtime_type is not None \
            and self.overtime_type is not None, \
            "Can only perform overlap comparison for overtimes that have " \
            "the overtime type defined."
        assert other.budget == self.budget, \
            "Can only perform overlap comparison between two overtimes " \
            "belonging to the same budget."
        assert other.overtime_type != self.overtime_type, \
            "Can only perform overlap comparison between two overtimes " \
            "that have different overtime type."

    def validate_before_save(self):
        pass
