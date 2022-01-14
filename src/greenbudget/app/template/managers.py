from greenbudget.app.budget.managers import BaseBudgetManager
from greenbudget.app.budget.duplication import duplicate
from greenbudget.app.tabling.query import RowQuerier, RowPolymorphicQuerySet


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
        from greenbudget.app.budget.models import Budget
        return duplicate(template, user,
            destination_cls=Budget,
            **overrides
        )
