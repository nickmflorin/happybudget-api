# pylint: disable=redefined-outer-name
import datetime
import mock
import plaid
import pytest

from greenbudget.app.actual.models import Actual
from greenbudget.app.integrations.plaid.api import client


@pytest.fixture
def mock_accounts():
    return [
        {
            "account_id": 1,
            'name': 'Savings Account',
            'official_name': 'My Savings Account',
            'type': 'depository',
            'subtype': 'savings'
        },
        {
            "account_id": 2,
            'name': 'Checking Account',
            'official_name': 'My Checking Account',
            'type': 'depository',
            'subtype': 'checking'
        },
        {
            "account_id": 3,
            'name': 'Credit Account',
            'official_name': 'My Credit Card Account',
            'type': 'credit',
            'subtype': 'credit card'
        }
    ]


@pytest.fixture
def mock_transactions():
    return [
        {
            "category": ["Food and Drink", "Restaurants"],
            "name": "SparkFun",
            "amount": 89.4,
            "date": datetime.date(2022, 1, 1),
            "datetime": None,
            "iso_currency_code": 'USD',
            "transaction_id": 1,
            "account_id": 3,
            "merchant_name": 'SparkFun'
        },
        {
            "category": ["Entertainment"],
            "name": "Dave & Busters",
            "amount": 10.0,
            "date": datetime.date(2022, 10, 5),
            "datetime": datetime.datetime(2022, 10, 5, 0, 0, 0),
            "iso_currency_code": 'USD',
            "transaction_id": 2,
            "account_id": 1,
            "merchant_name": 'Dave'
        },
        {
            "category": ["Restaurants"],
            "name": "Spinellis",
            "amount": 15.0,
            # Omitting the date should still cause the actual date to be
            # determined from the datetime.
            "date": None,
            "datetime": datetime.datetime(2022, 10, 6, 0, 0, 0),
            "iso_currency_code": 'USD',
            "transaction_id": 3,
            "account_id": 2,
            "merchant_name": 'Spinelli'
        },
        {
            "category": ["Restaurants"],
            "name": "Royal Forms",
            "amount": 11.0,
            # Omitting the date and datetime should cause the Actual not to have
            # an associated date.
            "date": None,
            "datetime": None,
            "account_id": 3,
            "iso_currency_code": 'USD',
            "transaction_id": 4,
            "merchant_name": 'RoFo'
        }
    ]


def test_bulk_import_actuals(api_client, user, budget_df, models, monkeypatch,
        mock_transactions, mock_accounts, create_actual_type):
    access_token_response = mock.MagicMock()
    access_token_response.access_token = "mock_access_token"

    transactions_response = mock.MagicMock()
    transactions_response.to_dict = lambda: {
        'transactions': mock_transactions,
        'accounts': mock_accounts
    }

    monkeypatch.setattr(
        client,
        'item_public_token_exchange',
        lambda *args: access_token_response
    )
    monkeypatch.setattr(
        client, 'transactions_get', lambda *args: transactions_response)

    plaid_tran_type = models.ActualType.PLAID_TRANSACTION_TYPES.credit_card
    actual_type = create_actual_type(
        title="Credit Card",
        color=None,
        plaid_transaction_type=plaid_tran_type
    )

    budget = budget_df.create_budget()
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-import-actuals/" % budget.pk,
        format="json",
        data={
            "start_date": "2021-12-31",
            "end_date": "2022-01-01",
            "account_ids": ["test-id1", "test-id2"],
            "source": Actual.IMPORT_SOURCES.bank_account,
            "public_token": "mock_public_token",
        }
    )
    actuals = models.Actual.objects.all()
    assert actuals.count() == 4
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
            "type": actuals[0].type,
            "value": 89.4,
            "actual_type": {
                "id": actual_type.pk,
                "order": actual_type.order,
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
            "type": actuals[1].type,
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
            "type": actuals[2].type,
            "value": 15.0,
            "actual_type": None,
        },
        {
            "id": actuals[3].pk,
            "name": "Royal Forms",
            "notes": "Restaurants",
            "order": actuals[3].order,
            "owner": None,
            "attachments": [],
            "contact": None,
            "date": None,
            "payment_id": actuals[3].payment_id,
            "purchase_order": actuals[3].purchase_order,
            "type": actuals[3].type,
            "value": 11.0,
            "actual_type": {
                "id": actual_type.pk,
                "order": actual_type.order,
                "color": None,
                "plural_title": None,
                "title": "Credit Card"
            }
        }
    ]


def test_bulk_import_actuals_plaid_error_token_exchange(create_budget, user,
        api_client):
    budget = create_budget()
    api_client.force_login(user)

    with mock.patch.object(client, 'item_public_token_exchange') as mocked:
        mocked.side_effect = plaid.ApiException()
        response = api_client.patch(
            "/v1/budgets/%s/bulk-import-actuals/" % budget.pk,
            format="json",
            data={
                "start_date": "2021-12-31",
                "end_date": "2022-01-01",
                "account_ids": ["test-id1", "test-id2"],
                "source": Actual.IMPORT_SOURCES.bank_account,
                "public_token": "mock_public_token",
            }
        )
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'There was an error retrieving the transactions.',
        'code': 'plaid_request_error',
        'error_type': 'bad_request'
    }]}


def test_bulk_import_actuals_plaid_error_transactions_get(create_budget, user,
        api_client, monkeypatch):
    access_token_response = mock.MagicMock()
    access_token_response.access_token = "mock_access_token"
    monkeypatch.setattr(
        client,
        'item_public_token_exchange',
        lambda *args: access_token_response
    )
    budget = create_budget()
    api_client.force_login(user)
    with mock.patch.object(client, 'transactions_get') as mocked:
        mocked.side_effect = plaid.ApiException()
        response = api_client.patch(
            "/v1/budgets/%s/bulk-import-actuals/" % budget.pk,
            format="json",
            data={
                "start_date": "2021-12-31",
                "account_ids": ["test-id1", "test-id2"],
                "end_date": "2022-01-01",
                "source": Actual.IMPORT_SOURCES.bank_account,
                "public_token": "mock_public_token",
            }
        )
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'There was an error retrieving the transactions.',
        'code': 'plaid_request_error',
        'error_type': 'bad_request'
    }]}


def test_bulk_import_actuals_with_template(api_client, user, template_df):
    budget = template_df.create_budget()
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-import-actuals/" % budget.pk,
        format="json",
        data={
            "start_date": "2021-12-31",
            "end_date": "2022-01-01",
            "account_ids": ["test-id1", "test-id2"],
            "source": Actual.IMPORT_SOURCES.bank_account,
            "public_token": "mock_public_token",
        }
    )
    assert response.status_code == 404


def test_bulk_import_actuals_end_date_before_start_date(api_client, user,
        budget_df):
    budget = budget_df.create_budget()
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-import-actuals/" % budget.pk,
        format="json",
        data={
            "start_date": "2021-12-31",
            "end_date": "2020-01-01",
            "account_ids": ["test-id1", "test-id2"],
            "source": Actual.IMPORT_SOURCES.bank_account,
            "public_token": "mock_public_token"
        }
    )
    assert response.status_code == 400
    assert response.json() == {"errors": [{
        "code": "invalid",
        "error_type": "field",
        "field": "start_date",
        "message": "The start date must be in the past and before the end date."
    }]}
