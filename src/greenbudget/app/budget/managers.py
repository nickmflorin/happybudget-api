from django.db import models


class BudgetQuerier(object):

    def active(self):
        # pylint: disable=no-member
        return self.filter(trash=False)

    def inactive(self):
        # pylint: disable=no-member
        return self.filter(trash=True)


class BudgetQuery(BudgetQuerier, models.query.QuerySet):
    pass


class BudgetManager(BudgetQuerier, models.Manager):
    queryset_class = BudgetQuery

    def get_queryset(self):
        return self.queryset_class(self.model)
