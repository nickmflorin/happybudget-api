from happybudget.app.user.query import ModelOwnershipQuerier
from happybudget.app.budgeting.query import BudgetAncestorQuerier
from happybudget.app.tabling.query import RowQuerySet


class MarkupQuerier(BudgetAncestorQuerier, ModelOwnershipQuerier):
    pass


class MarkupQuerySet(RowQuerySet, MarkupQuerier):
    pass
