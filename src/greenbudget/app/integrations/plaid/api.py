import collections
import datetime
import functools
import json
import logging

import plaid
from plaid.api import plaid_api
from plaid.model import (
    item_public_token_exchange_request,
    transactions_get_request,
    transactions_get_request_options,
    link_token_create_request,
    link_token_create_request_user,
    country_code,
    products
)

from django.conf import settings

from .models import PlaidTransaction, PlaidAccount
from .exceptions import PlaidRequestError


logger = logging.getLogger('greenbudget')


configuration = plaid.Configuration(
    host=settings.PLAID_ENVIRONMENT,
    api_key={
        'clientId': settings.PLAID_CLIENT_ID,
        'secret': settings.PLAID_CLIENT_SECRET
    }
)

api_client = plaid.ApiClient(configuration)


def obj_to_json(obj):
    # This is a temporary method we are using for logging.
    data = obj.to_dict()
    return_data = {}
    for k, v in data.items():
        if isinstance(v, datetime.date):
            return_data[k] = v.strftime('%Y-%m-%d')
        elif isinstance(v, datetime.datetime):
            return_data[k] = v.strftime('%Y-%m-%d, %H:%M:%S')
        else:
            try:
                json.dumps(v)
            except TypeError:
                if hasattr(v, 'to_dict'):
                    return_data[k] = obj_to_json(v)
            else:
                return_data[k] = v
    return json.dumps(return_data)


def raise_in_api_context(error_message):
    """
    Decorator for methods of :obj:`PlaidClient` that allow HTTP errors with
    Plaid's API to be raised in the context of our API.
    """
    def decorator(func):
        @functools.wraps(func)
        def decorated(instance, user, *args, **kwargs):
            raise_exception = kwargs.pop('raise_exception', False)
            if raise_exception:
                try:
                    return func(instance, user, *args, **kwargs)
                except plaid.ApiException as e:
                    logger.error(
                        "Plaid HTTP Error: An error occurred performing "
                        f"{func.__name__} for user {user.id}. Original error: "
                        f"\n{str(e)}.", extra={
                            'user_id': user.id,
                            'user_email': user.email,
                            'status': e.status
                        }
                    )
                    raise PlaidRequestError(error_message) from e
            return func(instance, user, *args, **kwargs)
        return decorated
    return decorator


GetTransactionsOptions = transactions_get_request_options\
    .TransactionsGetRequestOptions


class PlaidClient(plaid_api.PlaidApi):
    """
    Manages interactions with Plaid's API.

    An extension of :obj:`plaid.api.plaid_api.PlaidApi` that wraps relevant
    methods such that raised instances of :obj:`plaid.ApiException` can be
    raised in the API context such that standardized errors are rendered in
    the 400 response body.
    """
    @raise_in_api_context("There was an error exchanging the public token.")
    def exchange_public_token(self, user, public_token):
        """
        Exchanges the Plaid public token for an access token, which can be
        used to make requests to Plaid's API.
        """
        request = item_public_token_exchange_request \
            .ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.item_public_token_exchange(request)
        return response.access_token

    @raise_in_api_context("There was an error creating the link token.")
    def create_link_token(self, user):
        """
        Creates a link token for the given :obj:`User`.  The link token is
        used to open the Plaid Connect modal in the FE.
        """
        request = link_token_create_request.LinkTokenCreateRequest(
            client_name=settings.PLAID_CLIENT_NAME,
            language='en',
            country_codes=[country_code.CountryCode("US")],
            user=link_token_create_request_user.LinkTokenCreateRequestUser(
                str(user.id)),
            products=[products.Products("transactions")]
        )
        response = self.link_token_create(request)
        return response.link_token

    def log_duplicates(self, response):
        # This is a temporary check to determine why Plaid seems to be returning
        # duplicate transactions.
        already_seen = collections.defaultdict(list)

        for transaction in response.transactions:
            already_seen[(transaction.name, transaction.amount)].append(
                transaction)

        duplicates = [(k, v) for k, v in already_seen.items() if len(v) != 1]
        for (identifier, duplicate_list) in duplicates:
            jsonified = [obj_to_json(t) for t in duplicate_list]
            message = (
                "Plaid returned duplicate transactions for transaction name "
                f"{identifier[0]} with amount {identifier[1]}.  The duplicate "
                "transactions are as follows: \n" + "\n".join(jsonified)
            )
            logger.error(message)

    def _fetch_transactions(self, access_token, account_ids=None,
            option_kwargs=None, **kwargs):
        option_kwargs = option_kwargs or {}
        options = GetTransactionsOptions(**option_kwargs)
        if account_ids:
            options = GetTransactionsOptions(
                account_ids=account_ids,
                **option_kwargs
            )
        request = transactions_get_request.TransactionsGetRequest(
            access_token=access_token,
            options=options,
            **kwargs
        )
        response = self.transactions_get(request)
        self.log_duplicates(response)
        return response

    @raise_in_api_context("There was an error retrieving the transactions.")
    def fetch_transactions(self, user, **kwargs):
        """
        Fetches transactions for the given :obj:`User`.

        Parameters:
        ----------
        user: :obj:`User`
            The :obj:`User` instance for which to fetch transactions.

        access_token: :obj:`str` (optional)
            The Plaid access token that was previously generated via exchanging
            the Plaid public token with Plaid's API.  If not provided, the
            `public_token` must be provided.

            Default: None

        public_token: :obj:`str` (optional)
            The Plaid public token that was previously generated via the
            link token.  If provided, it will be used to generate the access
            token used in the request.  If not provided, the `access_token`
            must be provided explicitly.

            Default: None

        account_ids: :obj:`list` (optional)
            The IDs of the accounts for which the transactions should be
            requested for.  If omitted, the transactions for all associated
            accounts will be fetched.

            Default: []
        """
        public_token = kwargs.pop('public_token', None)
        access_token = kwargs.pop('access_token', None)
        account_ids = kwargs.pop('account_ids', None)

        assert 'start_date' in kwargs \
            and type(kwargs['start_date']) is datetime.date, \
            "The start date must be provided and it must be a valid " \
            f"{datetime.date} type."

        kwargs.setdefault('end_date', user.today_in_timezone)
        assert 'end_date' in kwargs \
            and type(kwargs['end_date']) is datetime.date, \
            "The end date must be provided and it must be a valid " \
            f"{datetime.date} type."

        assert public_token is not None or access_token is not None, \
            "Either the public token or access token must be provided."

        if access_token is None:
            access_token = self.exchange_public_token(user, public_token)

        response = self._fetch_transactions(
            access_token=access_token,
            account_ids=account_ids,
            **kwargs
        )
        accounts = [PlaidAccount(d) for d in response.accounts]
        transactions = [
            PlaidTransaction(user, accounts, d)
            for d in response.transactions
        ]
        # Plaid paginates their transaction responses, so we have to continue
        # making requests until we have received all of the transactions.
        while len(transactions) < response.total_transactions:
            response = self._fetch_transactions(
                access_token=access_token,
                account_ids=account_ids,
                option_kwargs={'offset': len(transactions)},
                **kwargs
            )
            transactions += [
                PlaidTransaction(user, accounts, d)
                for d in response.transactions
            ]

        # Right now, we are excluding pending transactions from the data because
        # Plaid seems to be including duplicate pending transactions with
        # different IDs.  Eventually we may want to include these, but for now
        # we want to exclude them and carefully log weird behavior to better
        # understand what is going on under the hood.
        return [t for t in transactions if t.pending is not True]


client = PlaidClient(api_client)
