from polymorphic.managers import PolymorphicManager

from greenbudget.lib.django_utils.models import BulkCreatePolymorphicQuerySet


class GroupQuerier(object):
    pass


class GroupQuery(GroupQuerier, BulkCreatePolymorphicQuerySet):
    pass


class GroupManager(GroupQuerier, PolymorphicManager):
    queryset_class = GroupQuery

    def get_queryset(self):
        return self.queryset_class(self.model)
