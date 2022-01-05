import logging

from .exceptions import StripeBadRequest
from . import stripe


logger = logging.getLogger('greenbudget')


def request_until_all_received(func, *args, **kwargs):
    """
    By default, Stripe will limit the number of results returned for a list
    endpoint to 100.  In some cases, we might also want to explicitly provide
    a lower limit.  In the cases that the number of results that exist exceeds
    this limit, the response will have a `has_more` attribute indicating that
    we need to send subsequent requests to get the rest of the data.

    For most of our use cases, this is an edge case - as it will be rare that
    we have more than 100 results unless we are retrieving data for all
    customers.  However, it is an important edge case to cover.

    TODO:
    ----
    We might need to account for RateLimitError(s) in the future.
    """
    all_results = []
    starting_after = None
    while True:
        kwargs['starting_after'] = starting_after
        results = func(*args, **kwargs)
        if len(results.data) == 0:
            break
        all_results += results.data
        if getattr(results, 'has_more', False) is True:
            starting_after = results.data[-1].id
        else:
            break
    return all_results


def get_products():
    try:
        products = request_until_all_received(stripe.Product.list, active=True)
    except stripe.error.InvalidRequestError as exc:
        logger.error(
            "Stripe HTTP Error: Could not retrieve products from Stripe.",
            extra={
                'error': "%s" % exc.error.to_dict(),
                "request_id": exc.request_id
            }
        )
        raise StripeBadRequest("Could not retrieve products from Stripe.")
    else:
        try:
            prices = request_until_all_received(stripe.Price.list)
        except stripe.error.InvalidRequestError as exc:
            logger.error(
                "Stripe HTTP Error: Could not retrieve prices from Stripe.",
                extra={
                    'error': "%s" % exc.error.to_dict(),
                    "request_id": exc.request_id
                }
            )
            raise StripeBadRequest("Could not retrieve prices from Stripe.")
        else:
            products_with_price = []
            for product in products:
                try:
                    price = [p for p in prices if p.product == product.id][0]
                except IndexError:
                    logger.error(
                        "Stripe Error: Could not find a price model associated "
                        "with product %s." % product.id,
                        extra={
                            "product": "%s" % product.to_dict_recursive(),
                        }
                    )
                    continue
                # Set the price_id on the product so it can be accessed by the
                # serializer.
                setattr(product, 'price_id', price.id)
                products_with_price.append(product)
            return products_with_price
