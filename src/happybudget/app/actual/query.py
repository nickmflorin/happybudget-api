from happybudget.app.user.query import ModelOwnershipQuerier
from happybudget.app.tabling.query import OrderedRowQuerySet, OrderedRowQuerier


class ActualQuerier(OrderedRowQuerier, ModelOwnershipQuerier):
    pass


class ActualQuerySet(OrderedRowQuerySet, ActualQuerier):
    pass
