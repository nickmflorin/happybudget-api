from polymorphic import models as polymorphic_models
from django.db import models

from .query import PolymorphicQuerySet, QuerySet


class PolymorphicManager(polymorphic_models.PolymorphicManager):
    queryset_class = PolymorphicQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model)


class Manager(models.Manager):
    queryset_class = QuerySet

    def get_queryset(self):
        return self.queryset_class(self.model)
