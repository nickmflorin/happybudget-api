# pylint: disable=redefined-outer-name
import datetime
import pytest
import mock

from happybudget.app.integrations.plaid.api import client
from happybudget.app.integrations.plaid.classification import PlaidCategories


@pytest.fixture
def patch_plaid_client_access_token(monkeypatch):
    access_token_response = mock.MagicMock()
    access_token_response.access_token = "mock_access_token"

    monkeypatch.setattr(
        client,
        'item_public_token_exchange',
        lambda *args: access_token_response
    )


@pytest.fixture
def plaid_transaction_response():
    def inner(mock_plaid_transactions, mock_plaid_accounts,
            total_transactions=None):
        response = mock.MagicMock()
        response.transactions = mock_plaid_transactions
        response.accounts = mock_plaid_accounts
        response.total_transactions = total_transactions \
            or len(mock_plaid_transactions)
        return response
    return inner


@pytest.fixture
def patch_plaid_transactions_response(monkeypatch, plaid_transaction_response,
        patch_plaid_client_access_token):
    def inner(mock_plaid_transactions, mock_plaid_accounts):
        response = plaid_transaction_response(mock_plaid_transactions,
            mock_plaid_accounts)
        monkeypatch.setattr(
            client, 'transactions_get', lambda *args: response)
    return inner


@pytest.fixture
def mock_plaid_accounts(mock_plaid):
    return [
        mock_plaid.Account(
            account_id='01',
            name='Savings Account',
            official_name='My Savings Account',
            type=mock_plaid.AccountType(value='depository'),
            subtype=mock_plaid.AccountSubType(value='savings'),
        ),
        mock_plaid.Account(
            account_id='02',
            name='Checking Account',
            official_name='My Checking Account',
            type=mock_plaid.AccountType(value='depository'),
            subtype=mock_plaid.AccountSubType(value='checking'),
        ),
        mock_plaid.Account(
            account_id='03',
            name='Credit Account',
            official_name='My Credit Card Account',
            type=mock_plaid.AccountType(value='credit'),
            subtype=mock_plaid.AccountSubType(value='credit card')
        ),
    ]


@pytest.fixture
def mock_plaid_transactions(mock_plaid, mock_plaid_accounts):
    return [
        mock_plaid.Transaction(
            category=["Food and Drink", "Restaurants"],
            name="SparkFun",
            amount=89.4,
            date=datetime.date(2022, 1, 1),
            transaction_id='01',
            account_id=mock_plaid_accounts[2].account_id,
            merchant_name='Spark Fun',
        ),
        mock_plaid.Transaction(
            category=["Entertainment"],
            name="Dave & Busters",
            amount=10.0,
            date=datetime.date(2022, 10, 5),
            datetime=datetime.datetime(2022, 10, 5, 0, 0, 0),
            transaction_id='02',
            account_id=mock_plaid_accounts[0].account_id,
            merchant_name='Dave',
        ),
        mock_plaid.Transaction(
            category=["Restaurants"],
            name="Spinellis",
            amount=15.0,
            date=datetime.date(2022, 10, 6),
            datetime=datetime.datetime(2022, 10, 6, 0, 0, 0),
            transaction_id='03',
            account_id=mock_plaid_accounts[1].account_id,
            merchant_name='Spinelli',
        ),
        mock_plaid.Transaction(
            category=["Restaurants"],
            name="Royal Farms",
            amount=11.0,
            date=datetime.date(2022, 10, 5),
            transaction_id='04',
            account_id=mock_plaid_accounts[2].account_id,
            merchant_name='Rofo',
        ),
        # This transaction should be ignored.
        mock_plaid.Transaction(
            category=PlaidCategories.BANK_FEES.data,
            name="Bank Fee",
            amount=11.0,
            date=datetime.date(2022, 1, 5),
            transaction_id='05',
            account_id=mock_plaid_accounts[2].account_id,
        ),
        # This transaction should be ignored.
        mock_plaid.Transaction(
            category=PlaidCategories.OVERDRAFT_FEES.data,
            name="Overdraft Fee",
            amount=100.0,
            date=datetime.date(2022, 1, 5),
            transaction_id='06',
            account_id=mock_plaid_accounts[2].account_id,
        ),
        mock_plaid.Transaction(
            category=PlaidCategories.CHECK_WITHDRAWAL.data,
            name="Check Withdrawal",
            amount=1000.0,
            date=datetime.date(2022, 3, 5),
            transaction_id='06',
            account_id=mock_plaid_accounts[1].account_id,
        ),
        mock_plaid.Transaction(
            category=PlaidCategories.ACH_TRANSFER.data,
            name="ACH Transfer",
            amount=4000.0,
            date=datetime.date(2021, 3, 5),
            transaction_id='07',
            account_id=mock_plaid_accounts[1].account_id,
        ),
        mock_plaid.Transaction(
            category=PlaidCategories.WIRE_TRANSFER.data,
            name="Wire Transfer",
            amount=9000.0,
            date=datetime.date(2021, 6, 5),
            transaction_id='08',
            account_id=mock_plaid_accounts[1].account_id,
        ),
        # Pending transactions should be excluded.
        mock_plaid.Transaction(
            category=PlaidCategories.WIRE_TRANSFER.data,
            name="Wire Transfer",
            amount=9000.0,
            pending=True,
            date=datetime.date(2021, 6, 5),
            transaction_id='09',
            account_id=mock_plaid_accounts[1].account_id,
        )
    ]


@pytest.fixture
def plaid_actual_types(models, f):
    plaid_credit_card_tp = models.ActualType.PLAID_TRANSACTION_TYPES.credit_card
    plaid_check_tp = models.ActualType.PLAID_TRANSACTION_TYPES.check
    plaid_ach_tp = models.ActualType.PLAID_TRANSACTION_TYPES.ach
    plaid_wire_tp = models.ActualType.PLAID_TRANSACTION_TYPES.wire
    return {
        'credit_card': f.create_actual_type(
            title="Credit Card",
            color=None,
            plaid_transaction_type=plaid_credit_card_tp
        ),
        'check': f.create_actual_type(
            title="Check",
            color=None,
            plaid_transaction_type=plaid_check_tp
        ),
        'ach': f.create_actual_type(
            title="ACH",
            color=None,
            plaid_transaction_type=plaid_ach_tp
        ),
        'wire': f.create_actual_type(
            title="Wire",
            color=None,
            plaid_transaction_type=plaid_wire_tp
        )
    }
