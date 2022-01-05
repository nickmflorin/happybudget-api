from datetime import datetime
import logging
import time

from django.utils.functional import cached_property

from .constants import BillingStatus, StripeSubscriptionStatus
from .utils import get_product_internal_id, request_until_all_received
from . import stripe


logger = logging.getLogger('greenbudget')


class cached_stripe_property(cached_property):
    """
    Extension of :obj:`django.utils.functional.cached_property` that allows
    us to denote that a given property on :obj:`StripeCustomer` is related to
    data from Stripe's API and should be cleared when a reload is warranted.
    """
    pass


class token_cached_stripe_property(cached_stripe_property):
    """
    Extension of :obj:`django.utils.functional.cached_property` that both

    (1) Denotes that the given property on :obj:`StripeCustomer` is related to
        data from Stripe's API and should be cleared when a reload is warranted.
    (2) Denotes that the given property on :obj:`StripeCustomer` should be
        cached in the request token to avoid redundant calls to Stripe's API
        on subsequent requests.

    This method descriptor can only be used for properties that return values
    that can be safely serialized.
    """
    pass


class StripeCustomer:

    def __init__(self, user):
        self.stripe_id = user.stripe_id
        self.user = user
        if self.stripe_id is None:
            raise Exception(
                "StripeCustomer cannot be instantiated without a valid "
                "stripe ID."
            )

    @cached_property
    def stripe_cached_properties(self):
        stripe_cached_attrs = []
        for attr in dir(self):
            if isinstance(
                    getattr(self.__class__, attr, None), cached_stripe_property):
                stripe_cached_attrs.append(attr)
        return stripe_cached_attrs

    @cached_property
    def stripe_token_cached_properties(self):
        stripe_cached_attrs = []
        for attr in dir(self):
            if isinstance(getattr(self.__class__, attr, None),
                    token_cached_stripe_property):
                stripe_cached_attrs.append(attr)
        return stripe_cached_attrs

    def token_properties(self):
        for attr in self.stripe_token_cached_properties:
            class_method = getattr(self.__class__, attr)
            if hasattr(class_method, 'token_key'):
                token_key = getattr(class_method, 'token_key')
                yield (attr, token_key)

    @classmethod
    def from_token(cls, token_obj, user):
        """
        Instantiates an instance of :obj:`StripeCustomer` for the provided
        user and prepopulates the cache with values from the user's JWT
        token.
        """
        stripe_customer = cls(user=user)
        stripe_customer.cache_from_token(token_obj)
        return stripe_customer

    def cache_from_token(self, token_obj):
        """
        Uses the current request's JWT token to populate cached property values
        in the instance's memory, in the case that those values are not already
        cached, in order to avoid repetitive calls to Stripe's API in between
        requests.
        """
        for attr, token_key in self.token_properties():
            # Only update the cached value with the value from the request
            # token if the value is not already cached (preventing a
            # a reload from Stripe's API to get the value).
            if attr not in self.__dict__ and token_key in token_obj:
                # Use the value stored in the request token for the cache
                # so we do not need to reload the value from Stripe's API.
                self.__dict__[attr] = token_obj[token_key]

    def flush_cache(self, keys=None):
        """
        Clears @cached_stripe_property(s) on the instance from local memory
        so that subsequent access of the property will force the cache to
        be reloaded from Stripe's API.
        """
        keys = keys or []
        properties = self.stripe_cached_properties[:]
        if keys:
            properties = [p for p in properties if p in keys]
        for attr in properties:
            self.__dict__.pop(attr, None)

    def reload(self):
        self.flush_cache()
        return self.data

    @cached_stripe_property
    def data(self):
        try:
            return stripe.Customer.retrieve(self.stripe_id, expand=[
                'default_source',
                'subscriptions'
            ])
        except stripe.error.InvalidRequestError as exc:
            # This exception shouldn't be raised, but if so we should log it
            # as it indicates a customer that somehow has an invalid stripe_id.
            logger.error(
                "Stripe HTTP Error: Could not retrieve customer information "
                "for user %s with Stripe ID %s.  This means that there is "
                "either a problem with Stripe's API or the customer ID is "
                "not valid." % (self.user.pk, self.stripe_id), extra={
                    'user_id': self.user.pk,
                    'email': self.user.email,
                    'error': "%s" % exc.error.to_dict(),
                    "request_id": exc.request_id
                }
            )

    @cached_stripe_property
    def subscription(self):
        # Right now, we are only supporting one subscription per user.
        if not (self.data and self.data.subscriptions.data):
            # By default, the Customer object only includes active subscriptions.
            # To retrieve cancelled subscriptions, we need to list the
            # subscriptions by customer.
            inactive_subscriptions = stripe.Subscription.list(
                customer=self.stripe_id,
                status='all',
                limit=1
            )
            if inactive_subscriptions:
                return inactive_subscriptions.data[0]
            return
        return self.data.subscriptions.data[0]

    @property
    def subscription_items(self):
        if self.subscription:
            return [
                obj
                for obj in self.subscription['items'].data
            ]
        return []

    @property
    def plans(self):
        return [sub_item.plan for sub_item in self.subscription_items]

    @property
    def plan(self):
        # Right now, we are only supporting a single Plan per user - but in
        # the future if we support multiple Plans per user, this will be the
        # data source.
        if self.plans:
            return self.plans[0]

    @property
    def plan_id(self):
        if self.plan:
            return self.plan.id

    @cached_stripe_property
    def stripe_status(self):
        """
        Returns a string representing the status of the Customer's account
        in Stripe.

        Will be one of the following values:

        (1) Incomplete:
            The initial automatic paymanet attempt failed on an account
            with `collection_method=charge_automatically`.
        (2) Incomplete Expired:
            An account that is in `incomplete` and the payments have failed
            for more than 23 hours.
        (3) Trialing:
            Account is in a temporary trial period.
        (4) Active
        (5) Past Due: A renewal payment has failed but Stripe is still trying.
        (6) Cancelled: Possible end state for a past due account.
        (7) Unpaid: Possible end state for a past due account.
        """
        if self.subscription:
            return self.subscription.status

    @token_cached_stripe_property
    def billing_status(self):
        """
        Returns a string representing the status of the Customer's account in
        Stripe that we map for our own internal purposes.

        The following statuses are used:

        (1) Active
        (2) Expired
        (3) Cancelled
        (4) Unsubscribed
        (5) None

        Note that the `incomplete` state is the state of a subscription before
        we have successfully charged the customer.  If the subscription is not
        paid after 24 hours, it disappears.  In a normal payment flow, the
        `incomplete` status should be resolved almost immediately - but until it
        is we don't actually have a subscription.
        """
        status = self.stripe_status
        current_ts = time.mktime(datetime.now().timetuple())

        if status in (
            StripeSubscriptionStatus.ACTIVE,
            StripeSubscriptionStatus.TRIALING,
            StripeSubscriptionStatus.PAST_DUE
        ):
            return BillingStatus.ACTIVE
        elif status in (
            StripeSubscriptionStatus.INCOMPLETE,
            StripeSubscriptionStatus.INCOMPLETE_EXPIRED
        ):
            return None
        elif status == StripeSubscriptionStatus.UNPAID:
            return BillingStatus.EXPIRED
        # Check expiration to distinguish between cancelled and expired
        # subscriptions.
        elif self.subscription \
                and self.subscription.current_period_end < current_ts:
            return BillingStatus.EXPIRED
        elif status == StripeSubscriptionStatus.CANCELLED:
            return BillingStatus.CANCELLED
        return None

    billing_status.token_key = 'billing_status'

    @cached_stripe_property
    def payment_methods(self):
        # This method is not being used at this time, but may be in the short
        # future.  We need to catch and handle request errors when we do
        # implement.
        payment_methods = request_until_all_received(
            func=stripe.Customer.list_payment_methods,
            sid=self.stripe_id,
            # Right now, we are only supporting card payment methods.
            type='card'
        )
        [setattr(pm, 'is_default', False) for pm in payment_methods]
        if len(payment_methods) != 0:
            if not self.data.invoice_settings.default_payment_method:
                setattr(payment_methods[0], 'is_default', True)
            else:
                default_payment_method = next((
                    pm for pm in payment_methods
                    if pm.id == self.data.invoice_settings.default_payment_method  # noqa
                ), None)
                if default_payment_method is None:
                    raise Exception(
                        "Expected invoice default payment method with ID %s "
                        "to be in set of payment methods but it was not."
                        % self.data.invoice_settings.default_payment_method
                    )
                setattr(default_payment_method, 'is_default', True)

        return payment_methods

    @property
    def default_payment_method(self):
        return next((pm for pm in self.payment_methods if pm.is_default is True))

    @token_cached_stripe_property
    def stripe_product_id(self):
        if self.plan:
            return self.plan.product

    @token_cached_stripe_property
    def product_id(self):
        if self.stripe_product_id:
            return get_product_internal_id(self.stripe_product_id)

    product_id.token_key = 'product_id'

    def modify(self, **kwargs):
        return stripe.Customer.modify(self.stripe_id, **kwargs)
