from django.conf import settings
import stripe
from stripe import Customer, Product, Subscription, SubscriptionSchedule  # noqa

from .stripe_customer import StripeCustomer  # noqa
from .constants import *  # noqa
from .config import *  # noqa

stripe.api_key = settings.STRIPE_API_SECRET
