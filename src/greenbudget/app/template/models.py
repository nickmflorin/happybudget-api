from django.db import models, IntegrityError

from greenbudget.app import signals
from greenbudget.app.budget.models import BaseBudget

from .managers import TemplateManager


@signals.model(flags='suppress_budget_update')
class Template(BaseBudget):
    type = "template"
    community = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    objects = TemplateManager()
    MAP_FIELDS_FROM_ORIGINAL = ('image', 'name')

    class Meta(BaseBudget.Meta):
        verbose_name = "Template"
        verbose_name_plural = "Templates"
        # Check constraint to ensure that only community templates can be
        # hidden.
        constraints = [models.CheckConstraint(
            name="%(app_label)s_%(class)s_hidden_only_for_community",
            check=(
                models.Q(community=True, hidden=False)
                | models.Q(community=True, hidden=True)
                | models.Q(community=False, hidden=False)
            )
        )]

    def save(self, *args, **kwargs):
        if self.community is True and not self.created_by.is_staff:
            raise IntegrityError(
                "Community templates can only be created by staff users.")
        return super().save(*args, **kwargs)
