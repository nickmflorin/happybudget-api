import functools
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


def raise_in_api_context(error_message):
    """
    Decorator for methods of :obj:`PlaidClient` that allow HTTP errors with
    Plaid's API to be raised in the context of our API.
    """
    def decorator(func):
        @functools.wraps(func)
        def decorated(client, user, *args, **kwargs):
            raise_exception = kwargs.pop('raise_exception', False)
            if raise_exception:
                try:
                    return func(client, user, *args, **kwargs)
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
                    raise PlaidRequestError(error_message)
            return func(client, user, *args, **kwargs)
        return decorated
    return decorator


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
        request = item_public_token_exchange_request.ItemPublicTokenExchangeRequest(  # noqa
            public_token=public_token
        )
        response = self.item_public_token_exchange(request)
        return response.access_token

    @raise_in_api_context("There was an error creating the link token.")
    def create_link_token(self, user):
        """
        This first token needed in for part of the Plaid flow.
        Sequence: Link Token -> Public Token -> Access Token
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
        """
        public_token = kwargs.pop('public_token', None)
        access_token = kwargs.pop('access_token', None)

        assert public_token is not None or access_token is not None, \
            "Either the public token or access token must be provided."

        if access_token is None:
            access_token = self.exchange_public_token(user, public_token)

        request = transactions_get_request.TransactionsGetRequest(
            access_token=access_token,
            options=transactions_get_request_options.TransactionsGetRequestOptions(),  # noqa
            **kwargs
        )
        response = client.transactions_get(request)
        return response.to_dict()['transactions']


client = PlaidClient(api_client)