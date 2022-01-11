from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions


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
    CHECKOUT_INCONSISTENT_EMAIL = "checkout_inconsistent_email"


class CheckoutError(exceptions.ParseError):
    error_type = 'billing'
    default_code = BillingErrorCodes.CHECKOUT_ERROR
    default_detail = _("There was a error during checkout.")


class InconsistentEmailCheckoutError(exceptions.ParseError):
    error_type = 'billing'
    default_code = BillingErrorCodes.CHECKOUT_INCONSISTENT_EMAIL
    default_detail = _(
        "The email that was used to checkout must be consistent with the "
        "email used for the account."
    )


class CheckoutSessionInactiveError(CheckoutError):
    default_code = BillingErrorCodes.CHECKOUT_SESSION_INACTIVE
    default_detail = _("There is not an active checkout session.")


class StripeBadRequest(exceptions.ParseError):
    error_type = 'billing'
    default_code = BillingErrorCodes.STRIPE_REQUEST_ERROR
    default_detail = _("There was a Stripe error.")
