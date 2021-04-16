from django.contrib.contenttypes.models import ContentType
from polymorphic.managers import PolymorphicManager


class BudgetAccountGroupManager(PolymorphicManager):

    def get_queryset(self):
        from greenbudget.app.budget.models import Budget
        budget_ctype_id = ContentType.objects.get_for_model(
            Budget, for_concrete_model=False)
        qs = self.queryset_class(
            self.model._meta.concrete_model, using=self._db)
        return qs.filter(parent__polymorphic_ctype_id=budget_ctype_id)


class TemplateAccountGroupManager(PolymorphicManager):

    def get_queryset(self):
        from greenbudget.app.template.models import Template
        template_ctype_id = ContentType.objects.get_for_model(
            Template, for_concrete_model=False)
        qs = self.queryset_class(
            self.model._meta.concrete_model, using=self._db)
        return qs.filter(parent__polymorphic_ctype_id=template_ctype_id)
