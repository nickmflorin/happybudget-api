from polymorphic.managers import PolymorphicManager

from greenbudget.app.budget.managers import (
    ModelTemplateManager, ModelDuplicateManager)


class BudgetAccountGroupManager(
        ModelDuplicateManager(ModelTemplateManager(PolymorphicManager))):
    template_cls = 'group.TemplateAccountGroup'


class BudgetSubAccountGroupManager(
        ModelDuplicateManager(ModelTemplateManager(PolymorphicManager))):
    template_cls = 'group.TemplateSubAccountGroup'


class TemplateAccountGroupManager(ModelDuplicateManager(PolymorphicManager)):
    pass


class TemplateSubAccountGroupManager(ModelDuplicateManager(PolymorphicManager)):
    pass
