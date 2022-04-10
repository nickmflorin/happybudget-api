# pylint: disable=redefined-outer-name
import datetime
import mock
import plaid
import pytest

from greenbudget.app.actual.models import Actual
from greenbudget.app.integrations.plaid.api import client
from greenbudget.app.integrations.plaid.classification import PlaidCategory


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
def mock_transactions(mock_plaid):
    return [
        mock_plaid.Transaction(
            category=["Food and Drink", "Restaurants"],
            name="SparkFun",
            amount=89.4,
            date=datetime.date(2022, 1, 1),
            datetime=None,
            iso_currency_code='USD',
            transaction_id='01',
            account_id='03',
            merchant_name='Spark Fun',
        ),
        mock_plaid.Transaction(
            category=["Entertainment"],
            name="Dave & Busters",
            amount=10.0,
            date=datetime.date(2022, 10, 5),
            datetime=datetime.datetime(2022, 10, 5, 0, 0, 0),
            iso_currency_code='USD',
            transaction_id='02',
            account_id='01',
            merchant_name='Dave',
        ),
        mock_plaid.Transaction(
            category=["Restaurants"],
            name="Spinellis",
            amount=15.0,
            date=datetime.date(2022, 10, 6),
            datetime=datetime.datetime(2022, 10, 6, 0, 0, 0),
            iso_currency_code='USD',
            transaction_id='03',
            account_id='02',
            merchant_name='Spinelli',
        ),
        mock_plaid.Transaction(
            category=["Restaurants"],
            name="Royal Farms",
            amount=11.0,
            date=datetime.date(2022, 10, 5),
            datetime=None,
            iso_currency_code='USD',
            transaction_id='04',
            account_id='03',
            merchant_name='Rofo',
        ),
        # This transaction should be ignored.
        mock_plaid.Transaction(
            category=PlaidCategory.BANK_FEES.native,
            name="Bank Fee",
            amount=11.0,
            date=datetime.date(2022, 1, 5),
            datetime=None,
            iso_currency_code='USD',
            transaction_id='05',
            account_id='03',
            merchant_name=None,
        ),
        # This transaction should be ignored.
        mock_plaid.Transaction(
            category=PlaidCategory.OVERDRAFT_FEES.native,
            name="Overdraft Fee",
            amount=100.0,
            date=datetime.date(2022, 1, 5),
            datetime=None,
            iso_currency_code='USD',
            transaction_id='06',
            account_id='03',
            merchant_name=None,
        ),
        mock_plaid.Transaction(
            category=PlaidCategory.CHECK_WITHDRAWAL.native,
            name="Check Withdrawal",
            amount=1000.0,
            date=datetime.date(2022, 3, 5),
            datetime=None,
            iso_currency_code='USD',
            transaction_id='06',
            account_id='02',
            merchant_name=None,
        ),
        mock_plaid.Transaction(
            category=PlaidCategory.ACH_TRANSFER.native,
            name="ACH Transfer",
            amount=4000.0,
            date=datetime.date(2021, 3, 5),
            datetime=None,
            iso_currency_code='USD',
            transaction_id='07',
            account_id='02',
            merchant_name=None,
        ),
        mock_plaid.Transaction(
            category=PlaidCategory.WIRE_TRANSFER.native,
            name="Wire Transfer",
            amount=9000.0,
            date=datetime.date(2021, 6, 5),
            datetime=None,
            iso_currency_code='USD',
            transaction_id='08',
            account_id='02',
            merchant_name=None,
        )
    ]


def test_bulk_import_actuals(api_client, user, budget_df, models, monkeypatch,
        mock_transactions, mock_accounts, create_actual_type):
    access_token_response = mock.MagicMock()
    access_token_response.access_token = "mock_access_token"

    transactions_response = mock.MagicMock()
    transactions_response.transactions = mock_transactions
    transactions_response.accounts = mock_accounts

    monkeypatch.setattr(
        client,
        'item_public_token_exchange',
        lambda *args: access_token_response
    )
    monkeypatch.setattr(
        client, 'transactions_get', lambda *args: transactions_response)

    plaid_credit_card_tp = models.ActualType.PLAID_TRANSACTION_TYPES.credit_card
    plaid_check_tp = models.ActualType.PLAID_TRANSACTION_TYPES.check
    plaid_ach_tp = models.ActualType.PLAID_TRANSACTION_TYPES.ach
    plaid_wire_tp = models.ActualType.PLAID_TRANSACTION_TYPES.wire
    credit_card_actual_type = create_actual_type(
        title="Credit Card",
        color=None,
        plaid_transaction_type=plaid_credit_card_tp
    )
    check_actual_type = create_actual_type(
        title="Check",
        color=None,
        plaid_transaction_type=plaid_check_tp
    )
    ach_actual_type = create_actual_type(
        title="ACH",
        color=None,
        plaid_transaction_type=plaid_ach_tp
    )
    wire_actual_type = create_actual_type(
        title="Wire",
        color=None,
        plaid_transaction_type=plaid_wire_tp
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
                "id": credit_card_actual_type.pk,
                "order": credit_card_actual_type.order,
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
                "id": credit_card_actual_type.pk,
                "order": credit_card_actual_type.order,
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
                "id": check_actual_type.pk,
                "order": check_actual_type.order,
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
                "id": ach_actual_type.pk,
                "order": ach_actual_type.order,
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
                "id": wire_actual_type.pk,
                "order": wire_actual_type.order,
                "color": None,
                "plural_title": None,
                "title": "Wire"
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
