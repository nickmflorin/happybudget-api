# pylint: disable=redefined-outer-name
import datetime
import mock
import plaid
import pytest

from greenbudget.app.actual.models import Actual
from greenbudget.app.integrations.plaid import client


@pytest.fixture
def mock_transactions():
    return [
        {
            "category": ["Food and Drink", "Restaurants"],
            "name": "SparkFun",
            "amount": 89.4,
            "date": datetime.date(2022, 1, 1),
        },
        {
            "category": ["Entertainment"],
            "name": "Dave & Busters",
            "amount": 10.0,
            "date": datetime.date(2022, 10, 5),
        }
    ]


def test_bulk_import_actuals(api_client, user, budget_df, models, monkeypatch,
        mock_transactions):
    access_token_response = mock.MagicMock()
    access_token_response.access_token = "mock_access_token"

    transactions_response = mock.MagicMock()
    transactions_response.to_dict = lambda: {'transactions': mock_transactions}

    monkeypatch.setattr(
        client,
        'item_public_token_exchange',
        lambda *args: access_token_response
    )
    monkeypatch.setattr(
        client, 'transactions_get', lambda *args: transactions_response)

    budget = budget_df.create_budget()
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-import-actuals/" % budget.pk,
        format="json",
        data={
            "start_date": "2021-12-31",
            "end_date": "2022-01-01",
            "account_ids": ["test-id1", "test-id2"],
            "source": Actual.IMPORT_SOURCES.plaid,
            "public_token": "mock_public_token",
        }
    )
    actuals = models.Actual.objects.all()
    assert actuals.count() == 2
    assert response.status_code == 200
    assert response.json()["children"] == [
        {
            "actual_type": actuals[0].actual_type,
            "attachments": [],
            "contact": None,
            "date": "2022-01-01 00:00:00",
            "id": actuals[0].pk,
            "name": "SparkFun",
            "notes": "Food and Drink, Restaurants",
            "order": actuals[0].order,
            "owner": None,
            "payment_id": actuals[0].payment_id,
            "purchase_order": actuals[0].purchase_order,
            "type": actuals[0].type,
            "value": 89.4
        },
        {
            "actual_type": actuals[1].actual_type,
            "attachments": [],
            "contact": None,
            "date": "2022-10-05 00:00:00",
            "id": actuals[1].pk,
            "name": "Dave & Busters",
            "notes": "Entertainment",
            "order": actuals[1].order,
            "owner": None,
            "payment_id": actuals[1].payment_id,
            "purchase_order": actuals[1].purchase_order,
            "type": actuals[1].type,
            "value": 10.0
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
                "source": Actual.IMPORT_SOURCES.plaid,
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
                "source": Actual.IMPORT_SOURCES.plaid,
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
            "source": Actual.IMPORT_SOURCES.plaid,
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
            "source": Actual.IMPORT_SOURCES.plaid,
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
