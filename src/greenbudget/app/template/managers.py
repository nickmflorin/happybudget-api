from greenbudget.app.budget.managers import BaseBudgetManager
from greenbudget.app.budget.duplication import duplicate
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

    def derive(self, template, user, **overrides):
        from greenbudget.app.account.models import BudgetAccount
        from greenbudget.app.budget.models import Budget
        from greenbudget.app.subaccount.models import BudgetSubAccount
        return duplicate(template, user,
            destination_cls=Budget,
            destination_account_cls=BudgetAccount,
            destination_subaccount_cls=BudgetSubAccount,
            **overrides
        )
