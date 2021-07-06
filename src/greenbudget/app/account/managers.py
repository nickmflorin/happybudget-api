from polymorphic.managers import PolymorphicManager

from greenbudget.lib.django_utils.models import BulkCreatePolymorphicQuerySet


class AccountQuerier(object):
    pass


class AccountQuery(AccountQuerier, BulkCreatePolymorphicQuerySet):
    pass


class AccountManager(AccountQuerier, PolymorphicManager):
    queryset_class = AccountQuery

    def get_queryset(self):
        return self.queryset_class(self.model)
