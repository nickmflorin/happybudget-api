from happybudget.app.budget.managers import BaseBudgetManager
from happybudget.app.budget.duplication import Duplicator
from happybudget.app.tabling.query import RowQuerier, RowPolymorphicQuerySet


class TemplateQuerier(RowQuerier):
    def user(self, user):
        return self.filter(community=False, created_by=user)

    def community(self):
        return self.filter(community=True)


class TemplateQuery(TemplateQuerier, RowPolymorphicQuerySet):
    pass


class TemplateManager(TemplateQuerier, BaseBudgetManager):
    queryset_class = TemplateQuery

    def derive(self, template, user, **overrides):
        # pylint: disable=import-outside-toplevel
        from happybudget.app.budget.models import Budget
        duplicator = Duplicator(template, destination_cls=Budget)
        return duplicator(user, **overrides)
