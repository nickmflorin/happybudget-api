from django.db import models

from greenbudget.lib.django_utils.models import PrePKBulkCreateQuerySet
from greenbudget.app.budget.query import BudgetAncestorQuerier


class MarkupQuerier(BudgetAncestorQuerier):
    pass


class MarkupQuery(MarkupQuerier, PrePKBulkCreateQuerySet):
    pass


class MarkupManager(MarkupQuerier, models.Manager):
    queryset_class = MarkupQuery

    def get_queryset(self):
        return self.queryset_class(self.model)
