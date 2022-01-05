def test_get_products(api_client, user, mock_stripe):
    products = [
        mock_stripe.Product.create(internal_id="greenbudget_standard"),
        mock_stripe.Product.create(internal_id="greenbudget_premium")
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
            "id": "greenbudget_standard",
            "active": True,
            "description": "STANDARD plan and pricing.",
            "name": "Greenbudget STANDARD",
            "stripe_id": products[0].id,
            "image": None,
            "price_id": prices[0].id
        },
        {
            "id": "greenbudget_premium",
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
    mock_stripe.Product.create(internal_id="greenbudget_standard")
    mock_stripe.Product.create(internal_id="greenbudget_premium")

    api_client.force_login(user)
    response = api_client.get("/v1/billing/products/")
    assert response.status_code == 200
    assert response.json()['count'] == 0


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
        'user_id': 1,
        'errors': [{
            'message': 'User is already a Stripe customer.',
            'code': 'permission_denied',
            'error_type': 'auth'
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
        'user_id': 1,
        'errors': [{
            'message': 'User is not a Stripe customer.',
            'code': 'permission_denied',
            'error_type': 'auth'
        }]
    }
