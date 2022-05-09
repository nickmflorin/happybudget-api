# pylint: disable=redefined-outer-name
import datetime
import mock
import plaid
from plaid.model import (
    transactions_get_request,
    transactions_get_request_options,
)
import pytest

from happybudget.app.actual.models import Actual
from happybudget.app.integrations.plaid.api import client


OptsCls = transactions_get_request_options.TransactionsGetRequestOptions


@pytest.fixture
def perform_request(api_client, user, f):
    def inner(budget=None, start_date=None, end_date=None):
        budget = budget or f.create_budget()
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


def test_bulk_import_actuals(models, mock_plaid_accounts, perform_request,
        mock_plaid_transactions, patch_plaid_transactions_response,
        plaid_actual_types):
    patch_plaid_transactions_response(
        mock_plaid_transactions, mock_plaid_accounts)
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
                "id": plaid_actual_types['credit_card'].pk,
                "order": plaid_actual_types['credit_card'].order,
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
                "id": plaid_actual_types['credit_card'].pk,
                "order": plaid_actual_types['credit_card'].order,
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
                "id": plaid_actual_types['check'].pk,
                "order": plaid_actual_types['check'].order,
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
                "id": plaid_actual_types['ach'].pk,
                "order": plaid_actual_types['ach'].order,
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
                "id": plaid_actual_types['wire'].pk,
                "order": plaid_actual_types['wire'].order,
                "color": None,
                "plural_title": None,
                "title": "Wire"
            }
        }
    ]


def test_bulk_import_actuals_paginated(mock_plaid_accounts, perform_request,
        mock_plaid_transactions, patch_plaid_client_access_token,
        plaid_transaction_response):
    with mock.patch.object(client, 'transactions_get') as mocked:
        mocked.side_effect = [
            plaid_transaction_response(
                mock_plaid_transactions=mock_plaid_transactions[:4],
                mock_plaid_accounts=mock_plaid_accounts,
                total_transactions=len(mock_plaid_transactions)
            ),
            plaid_transaction_response(
                mock_plaid_transactions=mock_plaid_transactions[4:],
                mock_plaid_accounts=mock_plaid_accounts,
                total_transactions=len(mock_plaid_transactions)
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
        models, mock_plaid, plaid_actual_types,
        patch_plaid_transactions_response):
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

    patch_plaid_transactions_response([transaction], [account])

    # Delete the ActualType associated with
    # ActualType.PLAID_TRANSACTION_TYPES.checking such that the mapping no
    # longer exists.
    plaid_actual_types["check"].delete()

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
        patch_plaid_client_access_token, perform_request):
    with mock.patch.object(client, 'transactions_get') as mocked:
        mocked.side_effect = plaid.ApiException()
        response = perform_request()
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'There was an error retrieving the transactions.',
        'code': 'plaid_request_error',
        'error_type': 'bad_request'
    }]}


def test_bulk_import_actuals_with_template(f, perform_request):
    budget = f.create_template()
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
