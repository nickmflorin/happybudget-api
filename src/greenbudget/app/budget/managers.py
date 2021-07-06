from polymorphic.managers import PolymorphicManager

from greenbudget.lib.django_utils.models import BulkCreatePolymorphicQuerySet


class BudgetQuerier(object):
    pass


class BudgetQuery(BudgetQuerier, BulkCreatePolymorphicQuerySet):
    pass


class BaseBudgetManager(BudgetQuerier, PolymorphicManager):
    queryset_class = BudgetQuery

    def get_queryset(self):
        return self.queryset_class(self.model)


class BudgetManager(BaseBudgetManager):
    pass
