from django.db import models

from greenbudget.lib.django_utils.models import PrePKBulkCreateQuerySet
from greenbudget.app.budget.query import BudgetAncestorQuerier


class GroupQuerier(BudgetAncestorQuerier):
    pass


class GroupQuery(GroupQuerier, PrePKBulkCreateQuerySet):
    pass


class GroupManager(GroupQuerier, models.Manager):
    queryset_class = GroupQuery

    def get_queryset(self):
        return self.queryset_class(self.model)
