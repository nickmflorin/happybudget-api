from django.db import models, IntegrityError

from greenbudget.app.budget.models import BaseBudget

from .managers import TemplateManager


class Template(BaseBudget):
    type = "template"
    community = models.BooleanField(default=False)
    objects = TemplateManager()

    class Meta(BaseBudget.Meta):
        verbose_name = "Template"
        verbose_name_plural = "Templates"

    def save(self, *args, **kwargs):
        if self.community is True and not self.created_by.is_staff:
            raise IntegrityError(
                "Community templates can only be created by staff users.")
        return super().save(*args, **kwargs)
