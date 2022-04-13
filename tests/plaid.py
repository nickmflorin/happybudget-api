import datetime
import pytest

from plaid.model.account_base import AccountBase
from plaid.model.account_balance import AccountBalance
from plaid.model.account_type import AccountType
from plaid.model.account_subtype import AccountSubtype
from plaid.model.location import Location
from plaid.model.transaction import Transaction
from plaid.model.payment_meta import PaymentMeta

from greenbudget.app.integrations.plaid.constants import PlaidCategoryGroup


class MockPlaidModel:
    """
    Base class for Plaid related models.  When extended, instantiating the
    extended model will result in a new instance of a model from the
    `plaid-python` SDK.  Default values can be defined such that specifying
    them is not required.
    """
    def __new__(cls, *args, **kwargs):
        base_cls = getattr(cls, 'base_cls')

        defaults = getattr(cls, 'defaults', {})

        def process_default(default_value):
            if (isinstance(default_value, type)
                    and issubclass(default_value, MockPlaidModel)) \
                    or hasattr(default_value, '__call__'):
                return default_value()
            return default_value

        # The `attribute_map` property is defined on the `plaid_python` model,
        # an informs us which attributes the model needs to be initialized
        # with.
        for k, _ in base_cls.attribute_map.items():
            if k not in kwargs:
                kwargs[k] = process_default(
                    defaults.get(k, getattr(cls, f'default_{k}', None)))
        return base_cls(*args, **kwargs)


class MockPlaidAccountBalance(MockPlaidModel):
    base_cls = AccountBalance
    usage = 'account_balance'
    defaults = {
        'available': 100.0,
        'current': 100.0,
        'limit': 200.0,
        'iso_currency_code': 'USD',
        'unofficial_currency_code': 'USD',
        'last_updated_datetime': datetime.datetime.now
    }


class MockPlaidAccountType(MockPlaidModel):
    base_cls = AccountType
    usage = 'AccountType'


class MockPlaidAccountSubType(MockPlaidModel):
    base_cls = AccountSubtype
    usage = 'AccountSubType'


class MockPlaidAccount(MockPlaidModel):
    base_cls = AccountBase
    usage = 'Account'
    defaults = {
        'verification_status': 'verified',
        'balances': MockPlaidAccountBalance
    }


class MockPlaidPaymentMeta(MockPlaidModel):
    base_cls = PaymentMeta
    usage = 'PaymentMeta'


class MockPlaidLocation(MockPlaidModel):
    base_cls = Location
    usage = 'Location'
    defaults = {
        'address': '920 L Street NW',
        'city': 'Washington',
        'region': 'District of Columbia',
        'postal_code': '20001',
        'country': 'United States',
        'lat': 1234.5,
        'lon': 1234.5,
        'store_number': '091239'
    }


class MockPlaidTransaction(MockPlaidModel):
    base_cls = Transaction
    usage = 'Transaction'
    defaults = {
        'pending': False,
        'payment_channel': 'mock_payment_channel',
        'payment_meta': MockPlaidPaymentMeta,
        'location': MockPlaidLocation,
        'transaction_type': PlaidCategoryGroup.SPECIAL,
        'iso_currency_code': 'USD',
    }


class MockPlaid:
    mock_models = [
        MockPlaidAccount,
        MockPlaidAccountBalance,
        MockPlaidAccountSubType,
        MockPlaidAccountType,
        MockPlaidLocation,
        MockPlaidTransaction,
        MockPlaidPaymentMeta
    ]

    def __getattr__(self, k):
        try:
            return [m for m in self.mock_models if m.usage == k][0]
        except IndexError as e:
            raise AttributeError(
                f"Attribute {k} does not exist on {self.__class__}.") from e


@pytest.fixture
def mock_plaid():
    return MockPlaid()
