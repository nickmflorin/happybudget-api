from django.db import models

from greenbudget.lib.django_utils.models import PrePKBulkCreateQuerySet


class ActualQuerier(object):
    pass


class ActualQuery(ActualQuerier, PrePKBulkCreateQuerySet):
    pass


class ActualManager(ActualQuerier, models.Manager):
    queryset_class = ActualQuery

    def get_queryset(self):
        return self.queryset_class(self.model)
