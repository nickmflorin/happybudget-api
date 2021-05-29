from django.db import models
from django.contrib.contenttypes.models import ContentType

from greenbudget.app.budget.models import Budget
from greenbudget.app.common.managers import (
    ModelTemplateManager, ModelDuplicateManager)
from greenbudget.app.template.models import Template


class FringeQuerier(object):

    def for_budgets(self):
        # pylint: disable=no-member
        ctype_id = ContentType.objects.get_for_model(Budget).id
        return self.filter(budget__polymorphic_ctype_id=ctype_id)

    def for_templates(self):
        # pylint: disable=no-member
        ctype_id = ContentType.objects.get_for_model(Template).id
        return self.filter(budget__polymorphic_ctype_id=ctype_id)


class FringeQuery(FringeQuerier, models.QuerySet):
    pass


class FringeManager(ModelDuplicateManager(
    FringeQuerier,
    ModelTemplateManager(models.Manager)
)):
    template_cls = 'fringe.Fringe'
    queryset_class = FringeQuery

    def get_queryset(self):
        return self.queryset_class(self.model)


class BudgetFringeManager(FringeManager):
    def get_queryset(self):
        return super().get_queryset().for_budgets()


class TemplateFringeManager(FringeManager):
    def get_queryset(self):
        return super().get_queryset().for_templates()
