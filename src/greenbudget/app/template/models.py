from greenbudget.app.budget.models import BaseBudget

from .managers import TemplateManager


class Template(BaseBudget):
    type = "template"
    objects = TemplateManager()

    class Meta(BaseBudget.Meta):
        verbose_name = "Template"
        verbose_name_plural = "Templates"
