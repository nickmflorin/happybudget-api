import logging

from plaid.model.account_base import AccountBase
from plaid.model.transaction import Transaction

from greenbudget.lib.utils import ensure_iterable
from .classification import (
    PlaidCategorization, TRANSACTION_CLASSIFICATIONS,
    TRANSACTION_IGNORE_CLASSIFICATIONS)


logger = logging.getLogger('greenbudget')


class PlaidAttribute:
    def __init__(self, plaid_attr, attr=None, getter=None):
        self._plaid_attr = plaid_attr
        self._attr = attr
        self._getter = getter

    @property
    def attr(self):
        return self._attr or self._plaid_attr

    def _get_from_model(self, model):
        if self._getter is not None:
            return self._getter(model)
        return getattr(model, self._plaid_attr)

    def _set_on_instance(self, instance, value):
        setattr(instance, f'_{self.attr}', value)

    def _set_from_model(self, instance, model):
        self._set_on_instance(instance, self._get_from_model(model))

    def _set_from_data(self, instance, *args, **kwargs):
        data = dict(*args, **kwargs)
        self._set_on_instance(instance, data[self._plaid_attr])

    def implement(self, instance, *args, **kwargs):
        if args and not isinstance(args[0], dict):
            self._set_from_model(instance, args[0])
        else:
            self._set_from_data(instance, *args, **kwargs)


class PlaidModel:
    attrs = []

    def __init__(self, *args, **kwargs):
        for attr in self.attrs:
            attr.implement(self, *args, **kwargs)

    @property
    def id(self):
        return self._id

    @property
    def plaid_counterpart(self):
        raise NotImplementedError()

    def __repr__(self):
        return str({
            a.attr: getattr(self, a.attr)
            for a in self.attrs
        })

    def __str__(self):
        return self.__repr__()

    @classmethod
    def ensure_models(cls, *args, models):
        return [m if isinstance(m, cls) else cls(*args, **m) for m in models]


class PlaidAccount(PlaidModel):
    attrs = [
        PlaidAttribute('account_id', attr='id'),
        PlaidAttribute('name'),
        PlaidAttribute('official_name'),
        PlaidAttribute('type', getter=lambda a: a.type.value),
        PlaidAttribute('subtype', getter=lambda a: a.subtype.value),
    ]
    plaid_counterpart = AccountBase

    @property
    def name(self):
        return self._name

    @property
    def official_name(self):
        return self._official_name

    @property
    def type(self):
        return self._type

    @property
    def subtype(self):
        return self._subtype


class PlaidTransaction(PlaidModel):
    attrs = [
        PlaidAttribute('transaction_id', attr='id'),
        PlaidAttribute('datetime'),
        PlaidAttribute('date'),
        PlaidAttribute('name'),
        PlaidAttribute('merchant_name'),
        PlaidAttribute('amount'),
        PlaidAttribute('iso_currency_code'),
        PlaidAttribute('account_id'),
        PlaidAttribute('category', attr='categories')
    ]
    plaid_counterpart = Transaction

    def __init__(self, user, accounts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._accounts = accounts
        self._user = user

    @property
    def accounts(self):
        return PlaidAccount.ensure_models(models=self._accounts)

    @property
    def account(self):
        filtered = [a for a in self.accounts if a.id == self.account_id]
        if not filtered:
            logger.error(
                f"Plaid's API returned {len(self.accounts)} but none of them "
                f"map to the account ID {self.account_id} associated with "
                "transaction {self.id}.", extra={
                    'user_id': self._user.pk,
                    'user_email': self._user.email,
                    'transaction_id': self.id,
                    'account_id': self.account_id,
                    'accounts': ', '.join([a.id for a in self.accounts])
                }
            )
            return None
        elif len(filtered) != 1:
            logger.error(
                f"Plaid's API returned multiple ({len(filtered)}) accounts "
                f"for the same account ID {self.account_id} for transaction "
                f"{self.id}.", extra={
                    'user_id': self._user.pk,
                    'user_email': self._user.email,
                    'transaction_id': self.id,
                    'account_id': self.account_id,
                    'accounts': ', '.join([a.id for a in self.accounts])
                }
            )
        return filtered[0]

    def is_category(self, *categories):
        categories = ensure_iterable(categories)
        assert all([isinstance(x, PlaidCategorization) for x in categories]), \
            "All provided categories must be instances of " \
            f"{PlaidCategorization}."
        return any([c == self.categories for c in categories])

    def is_category_or_subset_of(self, *categories):
        categories = ensure_iterable(categories)
        assert all([isinstance(x, PlaidCategorization) for x in categories]), \
            "All provided categories must be instances of " \
            f"{PlaidCategorization}."
        return any([
            c.is_equal_or_parent_of(self.categories) for c in categories])

    @property
    def classification(self):
        return TRANSACTION_CLASSIFICATIONS.classify(self)

    @property
    def should_ignore(self):
        return TRANSACTION_IGNORE_CLASSIFICATIONS.classify(self)

    @property
    def account_id(self):
        return self._account_id

    @property
    def iso_currency_code(self):
        return self._iso_currency_code

    @property
    def datetime(self):
        if self._datetime is not None:
            return self._user.in_timezone(self._datetime)
        elif self._date is not None:
            return self._user.in_timezone(self._date, force_datetime=True)
        return None

    @property
    def date(self):
        # The date property will never be None.
        return self._user.in_timezone(self._date)

    @property
    def amount(self):
        return self._amount

    @property
    def name(self):
        return self._name

    @property
    def merchant_name(self):
        return self._merchant_name

    @property
    def categories(self):
        return self._categories
