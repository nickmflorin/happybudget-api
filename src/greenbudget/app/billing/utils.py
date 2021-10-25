from stripe import Product

from .exceptions import UnconfiguredProductException
from . import stripe


def get_product_internal_id(product):
    id = product
    if not isinstance(product, Product):
        product = stripe.Product.retrieve(product)
    else:
        id = product.id
    if 'internal_id' not in product.metadata:
        raise UnconfiguredProductException(id)
    return product.metadata['internal_id']
