from happybudget.app.user.query import ModelOwnershipQuerier
from happybudget.app.tabling.query import (
    OrderedRowQuerier, OrderedRowPolymorphicQuerySet)


class AccountQuerier(OrderedRowQuerier, ModelOwnershipQuerier):
    pass


class AccountQuerySet(OrderedRowPolymorphicQuerySet, AccountQuerier):
    pass
