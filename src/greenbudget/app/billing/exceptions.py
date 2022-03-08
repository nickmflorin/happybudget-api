from django.utils.translation import gettext_lazy as _

from greenbudget.lib.utils import ensure_iterable
from greenbudget.app import permissions, exceptions

from .mixins import ProductPermissionIdMixin


class UnconfiguredProductException(Exception):
    def __init__(self, stripe_product_id):
        self.stripe_product_id = stripe_product_id

    def __str__(self):
        return "Stripe product %s is not configured with an internal ID." \
            % self.stripe_product_id


class BillingErrorCodes:
    STRIPE_REQUEST_ERROR = "stripe_request_error"
    CHECKOUT_ERROR = "checkout_error"
    CHECKOUT_SESSION_INACTIVE = "checkout_session_inactive"


class CheckoutError(exceptions.BadRequest):
    error_type = 'billing'
    default_code = BillingErrorCodes.CHECKOUT_ERROR
    default_detail = _("There was a error during checkout.")


class CheckoutSessionInactiveError(CheckoutError):
    default_code = BillingErrorCodes.CHECKOUT_SESSION_INACTIVE
    default_detail = _("There is not an active checkout session.")


class StripeBadRequest(exceptions.BadRequest):
    error_type = 'billing'
    default_code = BillingErrorCodes.STRIPE_REQUEST_ERROR
    default_detail = _("There was a Stripe error.")


class ProductPermissionError(
        ProductPermissionIdMixin, permissions.PermissionError):
    default_detail = _("The account is not subscribed to the correct product.")
    default_code = permissions.PermissionErrorCodes.PRODUCT_PERMISSION_ERROR

    def __init__(self, *args, **kwargs):
        self.products = kwargs.pop('products', '__any__')
        if self.products != '__any__':
            self.products = ensure_iterable(self.products)

        permission_id = kwargs.pop('permission_id', None)
        ProductPermissionIdMixin.__init__(self, permission_id=permission_id)
        permissions.PermissionError.__init__(self, *args, **kwargs)
