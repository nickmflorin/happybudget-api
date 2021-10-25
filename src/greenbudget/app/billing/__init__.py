from django.conf import settings
import stripe
from stripe import Customer, Product, Subscription, SubscriptionSchedule  # noqa

from .stripe_customer import StripeCustomer  # noqa

stripe.api_key = settings.STRIPE_API_SECRET
