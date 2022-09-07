from happybudget.app.tabling.query import OrderedRowQuerySet, OrderedRowQuerier
from happybudget.app.user.query import UserQuerySetMixin, ModelOwnershipQuerier


class ContactQuerier(
        UserQuerySetMixin, OrderedRowQuerier, ModelOwnershipQuerier):
    pass


class ContactQuerySet(ContactQuerier, OrderedRowQuerySet):
    pass
