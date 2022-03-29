import datetime
import mock
import plaid
from plaid.model import (
    item_public_token_exchange_request,
    transactions_get_request,
    transactions_get_request_options,
    link_token_create_request,
    link_token_create_request_user,
    country_code,
    products
)
import pytest

from django.test import override_settings

from greenbudget.app.integrations.plaid import client
from greenbudget.app.integrations.plaid.exceptions import PlaidRequestError


def test_exchange_public_token(user):
    mock_response = mock.MagicMock()
    mock_response.access_token = "test_access_token"

    with mock.patch.object(client, 'item_public_token_exchange') as mocked:
        mocked.side_effect = lambda req: mock_response
        access_token = client.exchange_public_token(user, "test_public_token")

    assert access_token == 'test_access_token'

    req = item_public_token_exchange_request \
        .ItemPublicTokenExchangeRequest(public_token='test_public_token')
    assert mocked.called
    assert mocked.call_args[0][0] == req


def test_exchange_public_token_error_raise_exception(user):
    with mock.patch.object(client, 'item_public_token_exchange') as mocked:
        mocked.side_effect = plaid.ApiException()
        with pytest.raises(PlaidRequestError):
            # pylint: disable=unexpected-keyword-arg
            client.exchange_public_token(
                user, "test_public_token", raise_exception=True)

    req = item_public_token_exchange_request \
        .ItemPublicTokenExchangeRequest(public_token='test_public_token')
    assert mocked.called
    assert mocked.call_args[0][0] == req


def test_exchange_public_token_error_no_raise_exception(user):
    with mock.patch.object(client, 'item_public_token_exchange') as mocked:
        mocked.side_effect = plaid.ApiException()
        with pytest.raises(plaid.ApiException):
            # pylint: disable=unexpected-keyword-arg
            client.exchange_public_token(
                user, "test_public_token", raise_exception=False)

    req = item_public_token_exchange_request \
        .ItemPublicTokenExchangeRequest(public_token='test_public_token')
    assert mocked.called
    assert mocked.call_args[0][0] == req


@override_settings(PLAID_CLIENT_NAME='Test Plaid Client Name')
def test_create_link_token(user, settings):
    mock_response = mock.MagicMock()
    mock_response.link_token = "test_link_token"

    with mock.patch.object(client, 'link_token_create') as mocked:
        mocked.side_effect = lambda req: mock_response
        link_token = client.create_link_token(user)

    assert link_token == 'test_link_token'

    req = link_token_create_request.LinkTokenCreateRequest(
        client_name='Test Plaid Client Name',
        language='en',
        country_codes=[country_code.CountryCode("US")],
        user=link_token_create_request_user.LinkTokenCreateRequestUser(
            str(user.id)),
        products=[products.Products("transactions")]
    )
    assert mocked.called
    assert mocked.call_args[0][0] == req


def test_create_link_token_error_raise_exception(user):
    with mock.patch.object(client, 'link_token_create') as mocked:
        mocked.side_effect = plaid.ApiException()
        with pytest.raises(PlaidRequestError):
            # pylint: disable=unexpected-keyword-arg
            client.create_link_token(user, raise_exception=True)

    assert mocked.called


def test_create_link_token_error_no_raise_exception(user):
    with mock.patch.object(client, 'link_token_create') as mocked:
        mocked.side_effect = plaid.ApiException()
        with pytest.raises(plaid.ApiException):
            # pylint: disable=unexpected-keyword-arg
            client.create_link_token(user, raise_exception=False)

    assert mocked.called


def test_fetch_transactions_with_public_token(user):
    mock_response = mock.MagicMock()
    mock_response.access_token = "test_access_token"

    mock_transactions_response = mock.MagicMock()
    mock_transactions_response.to_dict = lambda: {'transactions': []}

    with mock.patch.object(client, 'item_public_token_exchange') as mocked:
        mocked.side_effect = lambda req: mock_response
        with mock.patch.object(client, 'transactions_get') as mocked_t:
            mocked_t.side_effect = lambda req: mock_transactions_response
            transactions = client.fetch_transactions(
                user,
                public_token='test_public_token',
                start_date=datetime.date(2022, 1, 1),
                end_date=datetime.date(2022, 3, 1)
            )

    assert transactions == []

    # Since we are providing the public token, make sure the request to get the
    # access token was called.
    assert mocked.called

    req = transactions_get_request.TransactionsGetRequest(
        access_token='test_access_token',
        start_date=datetime.date(2022, 1, 1),
        end_date=datetime.date(2022, 3, 1),
        options=transactions_get_request_options
            .TransactionsGetRequestOptions(),
    )
    assert mocked_t.called
    assert mocked_t.call_args[0][0] == req


@override_settings(PLAID_CLIENT_NAME='Test Plaid Client Name')
def test_fetch_transactions_with_access_token(user):
    mock_transactions_response = mock.MagicMock()
    mock_transactions_response.to_dict = lambda: {'transactions': []}

    with mock.patch.object(client, 'item_public_token_exchange') as mocked:
        with mock.patch.object(client, 'transactions_get') as mocked_t:
            mocked_t.side_effect = lambda req: mock_transactions_response
            transactions = client.fetch_transactions(
                user,
                access_token='test_access_token',
                start_date=datetime.date(2022, 1, 1),
                end_date=datetime.date(2022, 3, 1)
            )

    assert transactions == []

    # Since we are providing the access token, the request to fetch another
    # access token should not be called.
    assert not mocked.called

    req = transactions_get_request.TransactionsGetRequest(
        access_token='test_access_token',
        start_date=datetime.date(2022, 1, 1),
        end_date=datetime.date(2022, 3, 1),
        options=transactions_get_request_options
            .TransactionsGetRequestOptions(),
    )
    assert mocked_t.called
    assert mocked_t.call_args[0][0] == req


def test_fetch_transactions_error_raise_exception(user):
    with mock.patch.object(client, 'transactions_get') as mocked:
        mocked.side_effect = plaid.ApiException()
        with pytest.raises(PlaidRequestError):
            client.fetch_transactions(
                user,
                access_token='test_access_token',
                start_date=datetime.date(2022, 1, 1),
                end_date=datetime.date(2022, 3, 1),
                raise_exception=True
            )
    assert mocked.called


def test_fetch_transactions_error_no_raise_exception(user):
    with mock.patch.object(client, 'transactions_get') as mocked:
        mocked.side_effect = plaid.ApiException()
        with pytest.raises(plaid.ApiException):
            client.fetch_transactions(
                user,
                access_token='test_access_token',
                start_date=datetime.date(2022, 1, 1),
                end_date=datetime.date(2022, 3, 1),
                raise_exception=False
            )
    assert mocked.called
