from polymorphic.managers import PolymorphicManager

from greenbudget.lib.django_utils.models import BulkCreatePolymorphicQuerySet


class AccountQuerier(object):

    def active(self):
        # pylint: disable=no-member
        return self.filter(budget__trash=False)

    def inactive(self):
        # pylint: disable=no-member
        return self.filter(budget__trash=True)


class AccountQuery(AccountQuerier, BulkCreatePolymorphicQuerySet):
    pass


class AccountManager(AccountQuerier, PolymorphicManager):
    queryset_class = AccountQuery

    def get_queryset(self):
        return self.queryset_class(self.model)
