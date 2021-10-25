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


def stripe_resource(object_type, prefix=None):
    def decorator(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            now = datetime.datetime.now()
            as_dict = kwargs.pop('as_dict', False)

            base_data = {
                'object': object_type,
                'live_mode': True,
                'metadata': {},
                'created': int(time.mktime(now.timetuple()))
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
def customer_base():
    return {
        "address": None,
        "balance": 0,
        "currency": "usd",
        "default_source": None,
        "delinquent": False,
        "description": None,
        "discount": None,
        "email": "",
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
    return {
        "active": True,
        "attributes": [],
        "description": "%s plan and pricing." % internal_id.upper(),
        "images": [],
        "metadata": {
            "internal_id": internal_id
        },
        "name": "Greenbudget %s" % internal_id.upper(),
        "package_dimensions": None,
        "shippable": None,
        "statement_descriptor": None,
        "tax_code": None,
        "type": "service",
        "unit_label": None,
        "updated": 1637174687,
        "url": None
    }


@stripe_resource(object_type="plan", prefix="price")
def plan_base(product_id):
    return {
        "product": product_id,
        "active": True,
        "aggregate_usage": None,
        "amount": 2000,
        "amount_decimal": "2000",
        "billing_scheme": "per_unit",
        "currency": "usd",
        "interval": "month",
        "interval_count": 1,
        "nickname": None,
        "tiers_mode": None,
        "transform_usage": None,
        "trial_period_days": None,
        "usage_type": "licensed"
    }


@stripe_resource(object_type="price", prefix="price")
def price_base(product_id):
    return {
        "product": product_id,
        "active": True,
        "billing_scheme": "per_unit",
        "created": 1635531407,
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
def subscription_item_base(product_id, subscription_id):
    return {
        "subscription": subscription_id,
        "billing_thresholds": None,
        "quantity": 1,
        "tax_rates": [],
        "plan": plan_base(product_id, as_dict=True),
        "price": price_base(product_id, as_dict=True),
    }


def billing_details():
    return {
        "address": {
            "city": "Los Angeles",
            "country": "US",
            "line1": "1 Saturation Blvd",
            "line2": "Apartment 1000",
            "postal_code": "10000",
            "state": "CA"
        },
        "email": "jens@saturation.io",
        "name": "Jens Jacob",
        "phone": "5555555555"
    }


@stripe_resource(object_type="payment_method", prefix="pm")
def payment_method_base(customer_id):
    return {
        "billing_details": billing_details(),
        "customer": customer_id,
        "type": "card",
        "card": {
            "brand": "visa",
            "checks": {
                "address_line1_check": None,
                "address_postal_code_check": "pass",
                "cvc_check": "pass"
            },
            "country": "US",
            "exp_month": 2,
            "exp_year": 2028,
            "fingerprint": "1kOHzEO5Y4UoMgPL",
            "funding": "credit",
            "generated_from": None,
            "last4": "4242",
            "networks": {
                "available": [
                    "visa"
                ],
                "preferred": None
            },
            "three_d_secure_usage": {
                "supported": True
            },
            "wallet": None
        }
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
def subscription_base(customer_id, product_id):
    subscription_id = object_id(prefix="sub")
    return {
        "id": subscription_id,
        "customer": customer_id,
        "application_fee_percent": None,
        "automatic_tax": {
            "enabled": False
        },
        "billing_cycle_anchor": 1636778518,
        "billing_thresholds": None,
        "cancel_at": None,
        "cancel_at_period_end": False,
        "canceled_at": None,
        "collection_method": "charge_automatically",
        "current_period_end": 1639370518,
        "current_period_start": 1636778518,
        "days_until_due": None,
        "default_payment_method": None,
        "default_source": None,
        "default_tax_rates": [],
        "discount": None,
        "ended_at": None,
        "items": list_object(
            data=[subscription_item_base(
                product_id,
                subscription_id,
                as_dict=True
            )],
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
        "plan": plan_base(product_id, as_dict=True),
        "quantity": 1,
        "schedule": None,
        "start_date": 1636778518,
        "status": "active",
        "transfer_data": None,
        "trial_end": None,
        "trial_start": None
    }


@pytest.fixture
def mock_stripe_resources():
    return {
        "customer": customer_base,
        "subscription": subscription_base,
        "product": product_base,
        "payment_method": payment_method_base
    }


@pytest.fixture
def mock_stripe_data():
    return {
        "customers": {},
        "subscriptions": {},
        "products": {},
        "payment_methods": {}
    }


@pytest.fixture
def mock_stripe(mock_stripe_resources, mock_stripe_data):

    def raise_resource_missing(id):
        raise stripe.error.InvalidRequestError(
            'No such resource: %s' % id, 'id', code='resource_missing')

    def customer_create(email, **kwargs):
        customer = mock_stripe_resources["customer"](**kwargs)
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

        subscription = mock_stripe_resources["subscription"](
            customer_id, product_id)
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

    def product_create(internal_id, **kwargs):
        product = mock_stripe_resources["product"](internal_id)
        mock_stripe_data["products"][product.id] = product
        return product

    def product_retrieve(obj_id, **kwargs):
        if obj_id not in mock_stripe_data["products"]:
            raise_resource_missing(obj_id)
        return mock_stripe_data["products"][obj_id]

    def product_list(**kwargs):
        products = list(mock_stripe_data["products"].values())
        return list_object(data=products)

    def payment_method_create(customer_id, **kwargs):
        payment_method = mock_stripe_resources["payment_method"](
            customer_id, **kwargs)
        mock_stripe_data["payment_methods"][payment_method.id] = payment_method
        return payment_method

    def payment_method_retrieve(obj_id, **kwargs):
        if obj_id not in mock_stripe_data["payment_methods"]:
            raise_resource_missing(obj_id)
        return mock_stripe_data["payment_methods"][obj_id]

    def payment_method_list(sid, type, **kwargs):
        payment_methods = [
            pm for pm in list(mock_stripe_data["payment_methods"].values())
            if pm.customer == sid and pm.type == type
        ]
        return list_object(data=payment_methods)

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
            mock.patch.object(stripe.Product, 'create',
                mock.Mock(wraps=product_create)), \
            mock.patch.object(stripe.Product, 'retrieve',
                mock.Mock(wraps=product_retrieve)), \
            mock.patch.object(stripe.Product, 'list',
                mock.Mock(wraps=product_list)), \
            mock.patch.object(stripe.PaymentMethod, 'create',
                mock.Mock(wraps=payment_method_create)), \
            mock.patch.object(stripe.PaymentMethod, 'retrieve',
                mock.Mock(wraps=payment_method_retrieve)), \
            mock.patch.object(stripe.Customer, 'list_payment_methods',
                mock.Mock(wraps=payment_method_list)):
        yield stripe
