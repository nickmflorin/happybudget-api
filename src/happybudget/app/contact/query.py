from happybudget.app.tabling.query import OrderedRowQuerySet, OrderedRowQuerier
from happybudget.app.user.query import UserQuerySetMixin


class ContactQuerier(UserQuerySetMixin, OrderedRowQuerier):
    pass


class ContactQuerySet(ContactQuerier, OrderedRowQuerySet):
    pass