from polymorphic.managers import PolymorphicManager
from polymorphic.query import PolymorphicQuerySet


class BudgetQuerier(object):

    def active(self):
        # pylint: disable=no-member
        return self.filter(trash=False)

    def inactive(self):
        # pylint: disable=no-member
        return self.filter(trash=True)


class BudgetQuery(BudgetQuerier, PolymorphicQuerySet):
    pass


class BudgetManager(BudgetQuerier, PolymorphicManager):
    queryset_class = BudgetQuery

    def get_queryset(self):
        return self.queryset_class(self.model)
