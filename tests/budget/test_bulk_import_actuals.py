# pylint: disable=redefined-outer-name
import datetime
import mock
import plaid
from plaid.model import (
    transactions_get_request,
    transactions_get_request_options,
)
import pytest

from greenbudget.app.actual.models import Actual
from greenbudget.app.integrations.plaid.api import client
from greenbudget.app.integrations.plaid.classification import PlaidCategories


OptsCls = transactions_get_request_options.TransactionsGetRequestOptions


@pytest.fixture
def patch_client_access_token(monkeypatch):
    access_token_response = mock.MagicMock()
    access_token_response.access_token = "mock_access_token"

    monkeypatch.setattr(
        client,
        'item_public_token_exchange',
        lambda *args: access_token_response
    )


@pytest.fixture
def transaction_response():
    def inner(mock_transactions, mock_accounts, total_transactions=None):
        response = mock.MagicMock()
        response.transactions = mock_transactions
        response.accounts = mock_accounts
        response.total_transactions = total_transactions \
            or len(mock_transactions)
        return response
    return inner


@pytest.fixture
def patch_transactions_response(monkeypatch, patch_client_access_token,
        transaction_response):
    def inner(mock_transactions, mock_accounts):
        response = transaction_response(mock_transactions, mock_accounts)
        monkeypatch.setattr(
            client, 'transactions_get', lambda *args: response)
    return inner


@pytest.fixture
def perform_request(api_client, user, budget_df):
    def inner(budget=None, start_date=None, end_date=None):
        budget = budget or budget_df.create_budget()
        api_client.force_login(user)
        return api_client.patch(
            "/v1/budgets/%s/bulk-import-actuals/" % budget.pk,
            format="json",
            data={
                "start_date": start_date or "2021-12-31",
                "end_date": end_date or "2022-01-01",
                "account_ids": ["test-id1", "test-id2"],
                "source": Actual.IMPORT_SOURCES.bank_account,
                # The public token doesn't matter because we patched the method
                # on the client responsible for exchanging the public token for
                # an access token.
                "public_token": "mock_public_token",
            }
        )
    return inner


@pytest.fixture
def mock_accounts(mock_plaid):
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
def mock_transactions(mock_plaid, mock_accounts):
    return [
        mock_plaid.Transaction(
            category=["Food and Drink", "Restaurants"],
            name="SparkFun",
            amount=89.4,
            date=datetime.date(2022, 1, 1),
            transaction_id='01',
            account_id=mock_accounts[2].account_id,
            merchant_name='Spark Fun',
        ),
        mock_plaid.Transaction(
            category=["Entertainment"],
            name="Dave & Busters",
            amount=10.0,
            date=datetime.date(2022, 10, 5),
            datetime=datetime.datetime(2022, 10, 5, 0, 0, 0),
            transaction_id='02',
            account_id=mock_accounts[0].account_id,
            merchant_name='Dave',
        ),
        mock_plaid.Transaction(
            category=["Restaurants"],
            name="Spinellis",
            amount=15.0,
            date=datetime.date(2022, 10, 6),
            datetime=datetime.datetime(2022, 10, 6, 0, 0, 0),
            transaction_id='03',
            account_id=mock_accounts[1].account_id,
            merchant_name='Spinelli',
        ),
        mock_plaid.Transaction(
            category=["Restaurants"],
            name="Royal Farms",
            amount=11.0,
            date=datetime.date(2022, 10, 5),
            transaction_id='04',
            account_id=mock_accounts[2].account_id,
            merchant_name='Rofo',
        ),
        # This transaction should be ignored.
        mock_plaid.Transaction(
            category=PlaidCategories.BANK_FEES.data,
            name="Bank Fee",
            amount=11.0,
            date=datetime.date(2022, 1, 5),
            transaction_id='05',
            account_id=mock_accounts[2].account_id,
        ),
        # This transaction should be ignored.
        mock_plaid.Transaction(
            category=PlaidCategories.OVERDRAFT_FEES.data,
            name="Overdraft Fee",
            amount=100.0,
            date=datetime.date(2022, 1, 5),
            transaction_id='06',
            account_id=mock_accounts[2].account_id,
        ),
        mock_plaid.Transaction(
            category=PlaidCategories.CHECK_WITHDRAWAL.data,
            name="Check Withdrawal",
            amount=1000.0,
            date=datetime.date(2022, 3, 5),
            transaction_id='06',
            account_id=mock_accounts[1].account_id,
        ),
        mock_plaid.Transaction(
            category=PlaidCategories.ACH_TRANSFER.data,
            name="ACH Transfer",
            amount=4000.0,
            date=datetime.date(2021, 3, 5),
            transaction_id='07',
            account_id=mock_accounts[1].account_id,
        ),
        mock_plaid.Transaction(
            category=PlaidCategories.WIRE_TRANSFER.data,
            name="Wire Transfer",
            amount=9000.0,
            date=datetime.date(2021, 6, 5),
            transaction_id='08',
            account_id=mock_accounts[1].account_id,
        ),
        # Pending transactions should be excluded.
        mock_plaid.Transaction(
            category=PlaidCategories.WIRE_TRANSFER.data,
            name="Wire Transfer",
            amount=9000.0,
            pending=True,
            date=datetime.date(2021, 6, 5),
            transaction_id='09',
            account_id=mock_accounts[1].account_id,
        )
    ]


@pytest.fixture
def actual_types(models, create_actual_type):
    plaid_credit_card_tp = models.ActualType.PLAID_TRANSACTION_TYPES.credit_card
    plaid_check_tp = models.ActualType.PLAID_TRANSACTION_TYPES.check
    plaid_ach_tp = models.ActualType.PLAID_TRANSACTION_TYPES.ach
    plaid_wire_tp = models.ActualType.PLAID_TRANSACTION_TYPES.wire
    return {
        'credit_card': create_actual_type(
            title="Credit Card",
            color=None,
            plaid_transaction_type=plaid_credit_card_tp
        ),
        'check': create_actual_type(
            title="Check",
            color=None,
            plaid_transaction_type=plaid_check_tp
        ),
        'ach': create_actual_type(
            title="ACH",
            color=None,
            plaid_transaction_type=plaid_ach_tp
        ),
        'wire': create_actual_type(
            title="Wire",
            color=None,
            plaid_transaction_type=plaid_wire_tp
        )
    }


def test_bulk_import_actuals(models, mock_accounts, mock_transactions,
        patch_transactions_response, actual_types, perform_request):
    patch_transactions_response(mock_transactions, mock_accounts)
    response = perform_request()

    actuals = models.Actual.objects.all()
    assert actuals.count() == 7
    assert response.status_code == 200
    assert response.json()["children"] == [
        {
            "id": actuals[0].pk,
            "name": "SparkFun",
            "notes": "Food and Drink, Restaurants",
            "attachments": [],
            "contact": None,
            "date": "2022-01-01",
            "order": actuals[0].order,
            "owner": None,
            "payment_id": actuals[0].payment_id,
            "purchase_order": actuals[0].purchase_order,
            "type": "actual",
            "value": 89.4,
            "actual_type": {
                "id": actual_types['credit_card'].pk,
                "order": actual_types['credit_card'].order,
                "color": None,
                "plural_title": None,
                "title": "Credit Card"
            }
        },
        {
            "id": actuals[1].pk,
            "name": "Dave & Busters",
            "notes": "Entertainment",
            "order": actuals[1].order,
            "attachments": [],
            "contact": None,
            "date": "2022-10-05",
            "owner": None,
            "payment_id": actuals[1].payment_id,
            "purchase_order": actuals[1].purchase_order,
            "type": "actual",
            "value": 10.0,
            "actual_type": None,
        },
        {
            "id": actuals[2].pk,
            "name": "Spinellis",
            "notes": "Restaurants",
            "attachments": [],
            "contact": None,
            "date": "2022-10-06",
            "order": actuals[2].order,
            "owner": None,
            "payment_id": actuals[2].payment_id,
            "purchase_order": actuals[2].purchase_order,
            "type": "actual",
            "value": 15.0,
            "actual_type": None,
        },
        {
            "id": actuals[3].pk,
            "name": "Royal Farms",
            "notes": "Restaurants",
            "order": actuals[3].order,
            "owner": None,
            "attachments": [],
            "contact": None,
            "date": "2022-10-05",
            "payment_id": actuals[3].payment_id,
            "purchase_order": actuals[3].purchase_order,
            "type": "actual",
            "value": 11.0,
            "actual_type": {
                "id": actual_types['credit_card'].pk,
                "order": actual_types['credit_card'].order,
                "color": None,
                "plural_title": None,
                "title": "Credit Card"
            }
        },
        {
            "id": actuals[4].pk,
            "name": "Check Withdrawal",
            "notes": "Transfer, Withdrawal, Check",
            "order": actuals[4].order,
            "owner": None,
            "attachments": [],
            "contact": None,
            "date": "2022-03-05",
            "payment_id": actuals[4].payment_id,
            "purchase_order": actuals[4].purchase_order,
            "type": "actual",
            "value": 1000.0,
            "actual_type": {
                "id": actual_types['check'].pk,
                "order": actual_types['check'].order,
                "color": None,
                "plural_title": None,
                "title": "Check"
            }
        },
        {
            "id": actuals[5].pk,
            "name": "ACH Transfer",
            "notes": "Transfer, ACH",
            "order": actuals[5].order,
            "owner": None,
            "attachments": [],
            "contact": None,
            "date": "2021-03-05",
            "payment_id": actuals[5].payment_id,
            "purchase_order": actuals[5].purchase_order,
            "type": "actual",
            "value": 4000.0,
            "actual_type": {
                "id": actual_types['ach'].pk,
                "order": actual_types['ach'].order,
                "color": None,
                "plural_title": None,
                "title": "ACH"
            }
        },
        {
            "id": actuals[6].pk,
            "name": "Wire Transfer",
            "notes": "Transfer, Wire",
            "order": actuals[6].order,
            "owner": None,
            "attachments": [],
            "contact": None,
            "date": "2021-06-05",
            "payment_id": actuals[6].payment_id,
            "purchase_order": actuals[6].purchase_order,
            "type": "actual",
            "value": 9000.0,
            "actual_type": {
                "id": actual_types['wire'].pk,
                "order": actual_types['wire'].order,
                "color": None,
                "plural_title": None,
                "title": "Wire"
            }
        }
    ]


def test_bulk_import_actuals_paginated(mock_accounts, mock_transactions,
        patch_client_access_token, perform_request, transaction_response):
    with mock.patch.object(client, 'transactions_get') as mocked:
        mocked.side_effect = [
            transaction_response(
                mock_transactions=mock_transactions[:4],
                mock_accounts=mock_accounts,
                total_transactions=len(mock_transactions)
            ),
            transaction_response(
                mock_transactions=mock_transactions[4:],
                mock_accounts=mock_accounts,
                total_transactions=len(mock_transactions)
            )
        ]
        perform_request()

    assert mocked.call_count == 2
    mocked.assert_has_calls([
        mock.call(transactions_get_request.TransactionsGetRequest(
            access_token='mock_access_token',
            options=OptsCls(
                account_ids=["test-id1", "test-id2"],
                count=500,
            ),
            start_date=datetime.date(2021, 12, 31),
            end_date=datetime.date(2022, 1, 1)
        )),
        mock.call(transactions_get_request.TransactionsGetRequest(
            access_token='mock_access_token',
            options=OptsCls(
                account_ids=["test-id1", "test-id2"],
                count=500,
                offset=4
            ),
            start_date=datetime.date(2021, 12, 31),
            end_date=datetime.date(2022, 1, 1)
        ))
    ])


def test_bulk_import_actuals_unconfigured_actual_type_map(perform_request,
        models, mock_plaid, actual_types, patch_transactions_response):
    # This account should cause the transaction to be classified as being
    # associated with ActualType.PLAID_TRANSACTION_TYPES.checking, which would
    # normally be mapped to an ActualType that is assigned to
    # ActualType.PLAID_TRANSACTION_TYPES.checking.  However, if we do not
    # assign an ActualType to ActualType.PLAID_TRANSACTION_TYPES.checking, then
    # the import should not fail - but rather the Actual created from the
    # transaction should simply not be linked to an ActualType.
    account = mock_plaid.Account(
        account_id='02',
        name='Checking Account',
        official_name='My Checking Account',
        # This will cause any transactions with this account to be associated
        # with ActualType.PLAID_TRANSACTION_TYPES.checking.
        type=mock_plaid.AccountType(value='depository'),
        subtype=mock_plaid.AccountSubType(value='checking'),
    )
    transaction = mock_plaid.Transaction(
        category=["Food and Drink", "Restaurants"],
        name="SparkFun",
        amount=89.4,
        date=datetime.date(2022, 1, 1),
        transaction_id='01',
        account_id=account.account_id,
        merchant_name='Spark Fun',
    )

    patch_transactions_response([transaction], [account])

    # Delete the ActualType associated with
    # ActualType.PLAID_TRANSACTION_TYPES.checking such that the mapping no
    # longer exists.
    actual_types["check"].delete()

    response = perform_request()

    actuals = models.Actual.objects.all()
    assert actuals.count() == 1
    assert response.status_code == 200
    assert response.json()["children"] == [{
        "id": actuals[0].pk,
        "name": "SparkFun",
        "notes": "Food and Drink, Restaurants",
        "attachments": [],
        "contact": None,
        "date": "2022-01-01",
        "order": actuals[0].order,
        "owner": None,
        "payment_id": actuals[0].payment_id,
        "purchase_order": actuals[0].purchase_order,
        "type": "actual",
        "value": 89.4,
        # The ActualType should not be linked since we removed the link between
        # the ActualType and ActualType.PLAID_TRANSACTION_TYPES.checking.
        "actual_type": None
    }]


def test_bulk_import_actuals_plaid_error_token_exchange(perform_request):
    with mock.patch.object(client, 'item_public_token_exchange') as mocked:
        mocked.side_effect = plaid.ApiException()
        response = perform_request()
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'There was an error retrieving the transactions.',
        'code': 'plaid_request_error',
        'error_type': 'bad_request'
    }]}


def test_bulk_import_actuals_plaid_error_transactions_get(
        patch_client_access_token, perform_request):
    with mock.patch.object(client, 'transactions_get') as mocked:
        mocked.side_effect = plaid.ApiException()
        response = perform_request()
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'There was an error retrieving the transactions.',
        'code': 'plaid_request_error',
        'error_type': 'bad_request'
    }]}


def test_bulk_import_actuals_with_template(template_df, perform_request):
    budget = template_df.create_budget()
    response = perform_request(budget)
    assert response.status_code == 404


def test_bulk_import_actuals_end_date_before_start_date(perform_request):
    response = perform_request(start_date="2021-12-31", end_date="2020-01-01")
    assert response.status_code == 400
    assert response.json() == {"errors": [{
        "code": "invalid",
        "error_type": "field",
        "field": "start_date",
        "message": "The start date must be in the past and before the end date."
    }]}
