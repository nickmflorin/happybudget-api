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


def stripe_resource(object_type, prefix=None):
    def decorator(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            as_dict = kwargs.pop('as_dict', False)
            base_data = {
                'object': object_type,
                'live_mode': True,
                'metadata': {},
                'created': now()
            }
            if prefix is not None:
                base_data['id'] = object_id(prefix=prefix)
            base_data.update(func(*args))
            base_data.update(**kwargs)
            if not as_dict:
                return convert_to_stripe_object(base_data)
            return base_data
        return inner
    return decorator


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


@stripe_resource(object_type="plan", prefix="price")
def plan_base(price, product):
    return {
        "product": product.id,
        "active": True,
        "aggregate_usage": None,
        "amount": price.unit_amount,
        "amount_decimal": price.unit_amount_decimal,
        "billing_scheme": price.billing_scheme,
        "currency": price.currenchy,
        "interval": "month",
        "interval_count": 1,
        "nickname": None,
        "tiers_mode": None,
        "transform_usage": None,
        "trial_period_days": None,
        "usage_type": "licensed"
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


@stripe_resource(object_type="subscription")
def subscription_base(plan, price, customer_id):
    subscription_id = object_id(prefix="sub")
    return {
        "id": subscription_id,
        "customer": customer_id,
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
            data=[subscription_item_base(plan, price, as_dict=True)],
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


@pytest.fixture
def mock_stripe_data():
    return {
        "customers": {},
        "subscriptions": {},
        "prices": {},
        "products": {}
    }


@pytest.fixture
def mock_stripe(mock_stripe_data):
    def raise_resource_missing(id):
        raise stripe.error.InvalidRequestError(
            'No such resource: %s' % id, 'id', code='resource_missing')

    def customer_create(email, **kwargs):
        customer = customer_base(**kwargs)
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

    def subscription_create(customer_id, product_id, **kwargs):
        customer = customer_retrieve(customer_id)
        product_retrieve(product_id)

        subscription = subscription_base(customer_id, product_id)
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
                mock.Mock(wraps=price_list)):
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
