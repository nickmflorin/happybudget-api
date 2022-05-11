import pytest


def test_get_products(api_client, user, mock_stripe):
    products = [
        mock_stripe.Product.create(internal_id="happybudget_standard"),
        mock_stripe.Product.create(internal_id="happybudget_premium")
    ]
    prices = [
        mock_stripe.Price.create(product_id=products[0].id),
        mock_stripe.Price.create(product_id=products[1].id),
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/billing/products/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": "happybudget_standard",
            "active": True,
            "description": "STANDARD plan and pricing.",
            "name": "Greenbudget STANDARD",
            "stripe_id": products[0].id,
            "image": None,
            "price_id": prices[0].id
        },
        {
            "id": "happybudget_premium",
            "active": True,
            "description": "PREMIUM plan and pricing.",
            "name": "Greenbudget PREMIUM",
            "stripe_id": products[1].id,
            "image": None,
            "price_id": prices[1].id
        }
    ]


def test_get_products_product_without_price_ommitted(api_client, user,
        mock_stripe):
    mock_stripe.Product.create(internal_id="happybudget_standard")
    mock_stripe.Product.create(internal_id="happybudget_premium")

    api_client.force_login(user)
    response = api_client.get("/v1/billing/products/")
    assert response.status_code == 200
    assert response.json()['count'] == 0


@pytest.mark.freeze_time('2020-01-01')
def test_get_user_subscription(api_client, standard_product_user):
    api_client.force_login(standard_product_user)
    response = api_client.get("/v1/billing/subscription/")
    assert response.json() == {
        'subscription': {
            'id': standard_product_user.stripe_customer.subscription.id,
            'cancel_at_period_end': False,
            'canceled_at': None,
            'cancel_at': None,
            'current_period_start': "2020-01-01 00:00:00",
            'current_period_end': "2020-01-01 00:00:00",
            'start_date': "2020-01-01 00:00:00",
            'status': 'active'
        }
    }


def test_checkout_session(api_client, user, mock_stripe_data, prices):
    api_client.force_login(user)
    response = api_client.post(
        "/v1/billing/checkout-session/", data={"price_id": prices[0].id})
    session_ids = list(mock_stripe_data['checkout_sessions'].keys())
    assert len(session_ids) == 1
    assert response.status_code == 200
    assert response.json() == {
        'redirect_url': 'https://checkout.stripe.com/pay/%s' % session_ids[0]
    }


def test_checkout_session_user_already_stripe_customer(api_client, user, prices,
        mock_stripe_data, stripe_customer):
    api_client.force_login(user)
    response = api_client.post(
        "/v1/billing/checkout-session/", data={"price_id": prices[0].id})
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'User is already a Stripe customer.',
            'code': 'permission_error',
            'error_type': 'permission'
        }]
    }
    session_ids = list(mock_stripe_data['checkout_sessions'].keys())
    assert len(session_ids) == 0


def test_portal_session(api_client, user, mock_stripe_data, stripe_customer):
    api_client.force_login(user)
    response = api_client.post("/v1/billing/portal-session/")
    session_ids = list(mock_stripe_data['portal_sessions'].keys())
    assert len(session_ids) == 1
    assert response.status_code == 200
    assert response.json() == {
        'redirect_url': 'https://billing.stripe.com/session/%s' % "1234"
    }


def test_portal_session_user_not_stripe_customer(api_client, user,
        mock_stripe_data):
    api_client.force_login(user)
    response = api_client.post("/v1/billing/portal-session/")
    session_ids = list(mock_stripe_data['portal_sessions'].keys())
    assert len(session_ids) == 0
    assert response.status_code == 403
    assert response.json() == {
        'errors': [{
            'message': 'User is not a Stripe customer.',
            'code': 'permission_error',
            'error_type': 'permission'
        }]
    }


def test_sync_checkout_session(api_client, user, mock_stripe_data, prices):
    # We have to create the checkout session via the API (instead of directly
    # via mock_stripe) because the Session ID needs to be stored in the request
    # session.
    api_client.force_login(user)

    response = api_client.post(
        "/v1/billing/checkout-session/", data={"price_id": prices[0].id})
    session_ids = list(mock_stripe_data['checkout_sessions'].keys())
    assert len(session_ids) == 1
    assert response.status_code == 200

    response = api_client.patch("/v1/billing/sync-checkout-session/", data={
        'session_id': session_ids[0]
    })
    # Note: The billing status and product_id will still be None, because those
    # will be added to the User's stripe information via Stripe during the
    # checkout process, not us - so we cannot make those assertions here.
    assert response.status_code == 200
    assert response.json()['id'] == user.id
