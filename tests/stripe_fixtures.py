import datetime
import functools
import mock
import pytest
import random
import string
import time

from stripe.util import convert_to_stripe_object

from greenbudget.app.billing import stripe


def object_id(prefix, length=8):
    return prefix + "_" + ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=length))


def now():
    return int(time.mktime(datetime.datetime.now().timetuple()))


def stripe_resource(object_type, prefix=None, required_kwargs=None):
    def decorated(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            as_dict = kwargs.pop('as_dict', False)
            base_data = {
                'object': object_type,
                'live_mode': True,
                'metadata': {},
                'created': now()
            }
            if prefix is not None:
                base_data['id'] = object_id(prefix=prefix)

            factory_kwargs = {}
            if required_kwargs is not None:
                for k in required_kwargs:
                    if k not in kwargs:
                        raise Exception(
                            'Factory %s missing keyword argument %s.'
                            % (func.__name__, k)
                        )
                    factory_kwargs[k] = kwargs.pop(k)

            base_data.update(func(*args, **factory_kwargs))
            base_data.update(**kwargs)
            if not as_dict:
                return convert_to_stripe_object(base_data)
            return base_data
        return wrapper
    return decorated


@pytest.fixture
def mock_stripe_data():
    return {
        "customers": {},
        "subscriptions": {},
        "prices": {},
        "products": {},
        "checkout_sessions": {},
        "portal_sessions": {},
        "plans": {}
    }


@pytest.fixture
def mock_stripe(mock_stripe_data):
    def raise_resource_missing(id):
        raise stripe.error.InvalidRequestError(
            'No such resource: %s' % id, 'id', code='resource_missing')

    @stripe_resource(
        object_type="billing_portal.session",
        prefix="bps",
        required_kwargs=["return_url", "customer"]
    )
    def portal_session_base(**kwargs):
        return {
            "configuration": object_id(prefix="bps"),
            "customer": kwargs["customer"],
            "locale": None,
            "on_behalf_of": None,
            "return_url": kwargs["return_url"],
            # This will be the Stripe URL that we redirect to.  I do not yet
            # understand why, but the ID in the PATH param does not seem to
            # correspond to anything we can predict for tests, so we keep it
            # a constant for now.
            "url": "https://billing.stripe.com/session/%s" % "1234"
        }

    @stripe_resource(
        object_type="checkout.session",
        prefix="cs",
        required_kwargs=["success_url", "cancel_url", "mode", "line_items"]
    )
    def checkout_session_base(**kwargs):
        id = object_id(prefix="cs")
        customer = customer_create("testemail@gmail.com")
        price = price_retrieve(kwargs['line_items'][0]['price'])
        return {
            "id": id,
            "subscription": object_id(prefix="sub"),
            "amount_subtotal": price.unit_amount,
            "amount_total": price.unit_amount,
            "cancel_url": kwargs['cancel_url'],
            "success_url": kwargs['success_url'],
            "customer": customer.id,
            "customer_details": {
                "email": customer.email,
                "phone": None,
                "tax_exempt": "none",
                "tax_ids": []
            },
            "after_expiration": None,
            "allow_promotion_codes": None,
            "automatic_tax": {
                "enabled": False,
                "status": None
            },
            "billing_address_collection": None,
            "client_reference_id": None,
            "consent": None,
            "consent_collection": None,
            "currency": "usd",
            "customer_email": None,
            "expires_at": now(),
            "locale": None,
            "metadata": {},
            "mode": kwargs['mode'],
            "payment_intent": None,
            "payment_method_options": {},
            "payment_method_types": ["card"],
            "payment_status": "paid",
            "phone_number_collection": {"enabled": False},
            "recovered_from": None,
            "setup_intent": None,
            "shipping": None,
            "shipping_address_collection": None,
            "shipping_options": [],
            "shipping_rate": None,
            "status": "complete",
            "submit_type": None,
            "total_details": {
                "amount_discount": 0,
                "amount_shipping": 0,
                "amount_tax": 0
            },
            # This will be the Stripe URL that we redirect to.
            "url": "https://checkout.stripe.com/pay/%s" % id
        }

    @stripe_resource(object_type="customer", prefix="cus")
    def customer_base(email):
        return {
            "address": None,
            "balance": 0,
            "currency": "usd",
            "default_source": None,
            "delinquent": False,
            "description": None,
            "discount": None,
            "email": email,
            "invoice_prefix": None,
            "tax_exempt": "none",
            "invoice_settings": {
                "custom_fields": None,
                "default_payment_method": None,
                "footer": None
            },
            "name": "",
            "next_invoice_sequence": None,
            "phone": None,
            "preferred_locales": [],
            "shipping": None,
            'subscriptions': {
                'object': 'list',
                'data': [],
                'has_more': False,
                'total_count': 0,
                'url': '/v1/customers/%s/subscriptions' % id,
            },
        }

    @stripe_resource(object_type="product", prefix="prod")
    def product_base(internal_id):
        slug = internal_id.split('_')[1]
        return {
            "active": True,
            "attributes": [],
            "description": "%s plan and pricing." % slug.upper(),
            "images": [],
            "metadata": {
                "internal_id": internal_id
            },
            "name": "Greenbudget %s" % slug.upper(),
            "package_dimensions": None,
            "shippable": None,
            "statement_descriptor": None,
            "tax_code": None,
            "type": "service",
            "unit_label": None,
            "updated": now(),
            "url": None
        }

    @stripe_resource(object_type="price", prefix="price")
    def price_base(product_id):
        return {
            "product": product_id,
            "active": True,
            "billing_scheme": "per_unit",
            "currency": "usd",
            "lookup_key": None,
            "nickname": None,
            "recurring": {
                "aggregate_usage": None,
                "interval": "month",
                "interval_count": 1,
                "trial_period_days": None,
                "usage_type": "licensed"
            },
            "tax_behavior": "unspecified",
            "tiers_mode": None,
            "transform_quantity": None,
            "type": "recurring",
            "unit_amount": 2000,
            "unit_amount_decimal": "2000"
        }

    @stripe_resource(object_type="subscription_item", prefix="si")
    def subscription_item_base(plan, price, subscription_id):
        return {
            "subscription": subscription_id,
            "billing_thresholds": None,
            "quantity": 1,
            "tax_rates": [],
            "plan": plan.to_dict_recursive(),
            "price": price.to_dict_recursive()
        }

    @stripe_resource(object_type="list")
    def list_object(**kwargs):
        return {
            'data': [],
            'has_more': False,
            'total_count': len(kwargs.get('data', [])),
            'url': '',
        }

    @stripe_resource(object_type="plan")
    def plan_base(price, product):
        return {
            "id": price.id,
            "active": True,
            "aggregate_usage": None,
            "amount": price.unit_amount,
            "amount_decimal": price.unit_amount_decimal,
            "billing_scheme": price.billing_scheme,
            "created": price.created,
            "currency": price.currency,
            "interval": price.recurring.interval,
            "interval_count": price.recurring.interval_count,
            "nickname": None,
            "product": product.id,
            "tiers_mode": price.tiers_mode,
            "transform_usage": None,
            "trial_period_days": price.recurring.trial_period_days,
            "usage_type": "licensed"
        }

    @stripe_resource(object_type="subscription")
    def subscription_base(plan, price, customer):
        subscription_id = object_id(prefix="sub")
        return {
            "id": subscription_id,
            "customer": customer.id,
            "application_fee_percent": None,
            "automatic_tax": {
                "enabled": False
            },
            "billing_cycle_anchor": now(),
            "billing_thresholds": None,
            "cancel_at": None,
            "cancel_at_period_end": False,
            "canceled_at": None,
            "collection_method": "charge_automatically",
            "current_period_end": now(),
            "current_period_start": now(),
            "days_until_due": None,
            "default_payment_method": None,
            "default_source": None,
            "default_tax_rates": [],
            "discount": None,
            "ended_at": None,
            "items": list_object(
                data=[subscription_item_base(
                    plan, price, subscription_id, as_dict=True)],
                url="/v1/subscription_items?subscription=%s" % subscription_id
            ),
            "latest_invoice": None,
            "next_pending_invoice_item_invoice": None,
            "pause_collection": None,
            "payment_settings": {
                "payment_method_options": None,
                "payment_method_types": None
            },
            "pending_invoice_item_interval": None,
            "pending_setup_intent": None,
            "pending_update": None,
            "plan": plan.to_dict_recursive(),
            "quantity": 1,
            "schedule": None,
            "start_date": now(),
            "status": "active",
            "transfer_data": None,
            "trial_end": None,
            "trial_start": None
        }

    def customer_create(email, **kwargs):
        customer = customer_base(email, **kwargs)
        mock_stripe_data["customers"][customer.id] = customer
        return customer

    def customer_retrieve(obj_id, **kwargs):
        if obj_id not in mock_stripe_data["customers"]:
            raise_resource_missing(obj_id)
        return mock_stripe_data["customers"][obj_id]

    def customer_modify(obj_id, **kwargs):
        if obj_id not in mock_stripe_data["customers"]:
            raise_resource_missing(obj_id)
        customer = mock_stripe_data["customers"][obj_id]
        for k, v in kwargs.items():
            if hasattr(customer[k], 'update'):
                customer[k].update(v)
            else:
                customer[k] = v
        return customer

    def subscription_create(plan, price, customer, **kwargs):
        subscription = subscription_base(plan, price, customer)
        mock_stripe_data["subscriptions"][subscription.id] = subscription
        customer.subscriptions.data.append(subscription)
        return subscription

    def subscription_retrieve(obj_id, **kwargs):
        if obj_id not in mock_stripe_data["subscriptions"]:
            raise_resource_missing(obj_id)
        return mock_stripe_data["subscriptions"][obj_id]

    def subscription_list(**kwargs):
        limit = kwargs.pop('limit', None)
        customer = kwargs.pop('customer', None)
        status = kwargs.pop('status', None)

        all_subscriptions = list(mock_stripe_data["subscriptions"].values())
        if customer:
            customer = customer_retrieve(customer)
            customer_subscription_ids = [
                subscription.id for subscription in customer.subscriptions.data
            ]
            all_subscriptions = [
                sub for sub in all_subscriptions
                if sub.id in customer_subscription_ids
            ]
        if status and status != 'all':
            all_subscriptions = [
                sub for sub in all_subscriptions
                if sub.status == status
            ]
        if limit:
            all_subscriptions = all_subscriptions[:limit]

        return list_object(data=all_subscriptions, url="/v1/subscriptions")

    def product_retrieve(obj_id, **kwargs):
        if obj_id not in mock_stripe_data["products"]:
            raise_resource_missing(obj_id)
        return mock_stripe_data["products"][obj_id]

    def product_list(**kwargs):
        products = list(mock_stripe_data["products"].values())
        return list_object(data=products)

    def product_create(internal_id, **kwargs):
        product = product_base(internal_id)
        mock_stripe_data["products"][product.id] = product
        return product

    def price_retrieve(obj_id, **kwargs):
        if obj_id not in mock_stripe_data["prices"]:
            raise_resource_missing(obj_id)
        return mock_stripe_data["prices"][obj_id]

    def price_list(**kwargs):
        prices = list(mock_stripe_data["prices"].values())
        return list_object(data=prices)

    def price_create(product_id, **kwargs):
        price = price_base(product_id)
        mock_stripe_data["prices"][price.id] = price
        return price

    def plan_retrieve(obj_id, **kwargs):
        if obj_id not in mock_stripe_data["plans"]:
            raise_resource_missing(obj_id)
        return mock_stripe_data["plans"][obj_id]

    def plan_list(**kwargs):
        plans = list(mock_stripe_data["plans"].values())
        return list_object(data=plans)

    def plan_create(price, product, **kwargs):
        plan = plan_base(price, product, **kwargs)
        mock_stripe_data["plans"][plan.id] = plan
        return plan

    def checkout_session_create(*args, **kwargs):
        session = checkout_session_base(*args, **kwargs)
        mock_stripe_data["checkout_sessions"][session.id] = session
        return session

    def checkout_session_retrieve(obj_id, **kwargs):
        if obj_id not in mock_stripe_data["checkout_sessions"]:
            raise_resource_missing(obj_id)
        return mock_stripe_data["checkout_sessions"][obj_id]

    def portal_session_create(*args, **kwargs):
        session = portal_session_base(*args, **kwargs)
        mock_stripe_data["portal_sessions"][session.id] = session
        return session

    def portal_session_retrieve(obj_id, **kwargs):
        if obj_id not in mock_stripe_data["portal_sessions"]:
            raise_resource_missing(obj_id)
        return mock_stripe_data["portal_sessions"][obj_id]

    with mock.patch.object(stripe.Customer, 'retrieve',
                mock.Mock(wraps=customer_retrieve)), \
            mock.patch.object(stripe.Customer, 'create',
                mock.Mock(wraps=customer_create)), \
            mock.patch.object(stripe.Customer, 'modify',
                mock.Mock(wraps=customer_modify)), \
            mock.patch.object(stripe.Subscription, 'list',
                mock.Mock(wraps=subscription_list)), \
            mock.patch.object(stripe.Subscription, 'create',
                mock.Mock(wraps=subscription_create)), \
            mock.patch.object(stripe.Subscription, 'retrieve',
                mock.Mock(wraps=subscription_retrieve)), \
            mock.patch.object(stripe.Product, 'retrieve',
                mock.Mock(wraps=product_retrieve)), \
            mock.patch.object(stripe.Product, 'list',
                mock.Mock(wraps=product_list)), \
            mock.patch.object(stripe.Product, 'create',
                mock.Mock(wraps=product_create)), \
            mock.patch.object(stripe.Price, 'retrieve',
                mock.Mock(wraps=price_retrieve)), \
            mock.patch.object(stripe.Price, 'create',
                mock.Mock(wraps=price_create)), \
            mock.patch.object(stripe.Price, 'list',
                mock.Mock(wraps=price_list)), \
            mock.patch.object(stripe.Plan, 'retrieve',
                mock.Mock(wraps=plan_retrieve)), \
            mock.patch.object(stripe.Plan, 'create',
                mock.Mock(wraps=plan_create)), \
            mock.patch.object(stripe.Plan, 'list',
                mock.Mock(wraps=plan_list)), \
            mock.patch.object(stripe.checkout.Session, 'retrieve',
                mock.Mock(wraps=checkout_session_retrieve)), \
            mock.patch.object(stripe.checkout.Session, 'create',
                mock.Mock(wraps=checkout_session_create)), \
            mock.patch.object(stripe.billing_portal.Session, 'retrieve',
                mock.Mock(wraps=portal_session_retrieve)), \
            mock.patch.object(stripe.billing_portal.Session, 'create',
                mock.Mock(wraps=portal_session_create)):
        yield stripe


@pytest.fixture
def products(mock_stripe):
    return [
        mock_stripe.Product.create("greenbudget_standard"),
        mock_stripe.Product.create("greenbudget_premium")
    ]


@pytest.fixture
def prices(mock_stripe, products):
    return [mock_stripe.Price.create(p.id) for p in products]


@pytest.fixture
def stripe_customer(user, mock_stripe):
    stripe_customer = mock_stripe.Customer.create(email=user.email)
    user.stripe_id = stripe_customer.id
    user.save()
    return stripe_customer


@pytest.fixture
def standard_product_user(user, products, prices, mock_stripe):
    stripe_customer = mock_stripe.Customer.create(email=user.email)
    plan = mock_stripe.Plan.create(prices[0], products[0])
    mock_stripe.Subscription.create(plan, prices[0], stripe_customer)
    user.stripe_id = stripe_customer.id
    user.save()
    return user
