from greenbudget.app.budget.managers import BaseBudgetManager
from greenbudget.app.budgeting.query import BudgetingPolymorphicQuerySet


class TemplateQuerier:
    def user(self, user):
        # pylint: disable=no-member
        return self.filter(community=False, created_by=user)

    def community(self):
        # pylint: disable=no-member
        return self.filter(community=True)


class TemplateQuery(TemplateQuerier, BudgetingPolymorphicQuerySet):
    pass


class TemplateManager(TemplateQuerier, BaseBudgetManager):
    queryset_class = TemplateQuery
