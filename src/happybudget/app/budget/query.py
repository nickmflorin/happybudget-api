from happybudget.app.user.query import ModelOwnershipQuerier
from happybudget.app.query import PolymorphicQuerySet


class BudgetQuerier(ModelOwnershipQuerier):
    pass


class BudgetQuerySet(PolymorphicQuerySet, BudgetQuerier):
    pass
