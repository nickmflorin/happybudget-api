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
