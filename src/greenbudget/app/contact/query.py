from greenbudget.app.tabling.query import OrderedRowQuerySet, OrderedRowQuerier
from greenbudget.app.user.query import UserQuerySetMixin


class ContactQuerier(UserQuerySetMixin, OrderedRowQuerier):
    pass


class ContactQuerySet(ContactQuerier, OrderedRowQuerySet):
    pass
