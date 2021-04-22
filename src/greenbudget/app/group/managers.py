from polymorphic.managers import PolymorphicManager

from greenbudget.app.budget.managers import ModelTemplateManager


class BudgetAccountGroupManager(ModelTemplateManager(PolymorphicManager)):
    template_cls = 'group.TemplateAccountGroup'


class BudgetSubAccountGroupManager(ModelTemplateManager(PolymorphicManager)):
    template_cls = 'group.TemplateSubAccountGroup'
