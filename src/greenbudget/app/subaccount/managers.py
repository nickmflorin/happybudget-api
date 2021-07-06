from polymorphic.managers import PolymorphicManager

from greenbudget.lib.django_utils.models import BulkCreatePolymorphicQuerySet


class SubAccountQuerier(object):
    pass


class SubAccountQuery(SubAccountQuerier, BulkCreatePolymorphicQuerySet):
    pass


class SubAccountManager(SubAccountQuerier, PolymorphicManager):
    queryset_class = SubAccountQuery

    def get_queryset(self):
        return self.queryset_class(self.model)
