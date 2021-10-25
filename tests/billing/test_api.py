def test_get_products(api_client, user, mock_stripe):
    products = [
        mock_stripe.Product.create(internal_id="standard"),
        mock_stripe.Product.create(internal_id="premium")
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/billing/products/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": "standard",
            "active": True,
            "description": "STANDARD plan and pricing.",
            "name": "Greenbudget STANDARD",
            "stripe_id": products[0].id,
            "image": None
        },
        {
            "id": "premium",
            "active": True,
            "description": "PREMIUM plan and pricing.",
            "name": "Greenbudget PREMIUM",
            "stripe_id": products[1].id,
            "image": None
        }
    ]


def test_get_payment_methods(api_client, standard_product_user, mock_stripe):
    payment_methods = [
        mock_stripe.PaymentMethod.create(standard_product_user.stripe_id),
        mock_stripe.PaymentMethod.create(standard_product_user.stripe_id)
    ]
    api_client.force_login(standard_product_user)
    response = api_client.get('/v1/billing/payment-methods/')
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": payment_methods[0].id,
            "type": "card",
            "is_default": True,
            "billing_details": {
                "email": payment_methods[0].billing_details.email,
                "name": payment_methods[0].billing_details.name,
                "phone": payment_methods[0].billing_details.phone,
                "address": {
                    "city": payment_methods[0].billing_details.address.city,
                    "country": payment_methods[0].billing_details.address.country,  # noqa
                    "line1": payment_methods[0].billing_details.address.line1,
                    "line2": payment_methods[0].billing_details.address.line2,
                    "state": payment_methods[0].billing_details.address.state,
                    "postal_code": int(payment_methods[0].billing_details.address.postal_code),  # noqa
                }
            },
            "card": {
                "last4": payment_methods[0].card.last4,
                "address_line1_check": payment_methods[0].card.checks.address_line1_check,  # noqa
                "address_postal_code_check": payment_methods[0].card.checks.address_postal_code_check,  # noqa
                "cvc_check": payment_methods[0].card.checks.cvc_check,
                "brand": payment_methods[0].card.brand,
                "country": payment_methods[0].card.country,
                "exp_month": payment_methods[0].card.exp_month,
                "exp_year": payment_methods[0].card.exp_year,
                "funding": payment_methods[0].card.funding,
            }
        },
        {
            "id": payment_methods[1].id,
            "type": "card",
            "is_default": False,
            "billing_details": {
                "email": payment_methods[1].billing_details.email,
                "name": payment_methods[1].billing_details.name,
                "phone": payment_methods[1].billing_details.phone,
                "address": {
                    "city": payment_methods[1].billing_details.address.city,
                    "country": payment_methods[1].billing_details.address.country,  # noqa
                    "line1": payment_methods[1].billing_details.address.line1,
                    "line2": payment_methods[1].billing_details.address.line2,
                    "state": payment_methods[1].billing_details.address.state,
                    "postal_code": int(payment_methods[1].billing_details.address.postal_code),  # noqa
                }
            },
            "card": {
                "last4": payment_methods[1].card.last4,
                "address_line1_check": payment_methods[1].card.checks.address_line1_check,  # noqa
                "address_postal_code_check": payment_methods[1].card.checks.address_postal_code_check,  # noqa
                "cvc_check": payment_methods[1].card.checks.cvc_check,
                "brand": payment_methods[1].card.brand,
                "country": payment_methods[1].card.country,
                "exp_month": payment_methods[1].card.exp_month,
                "exp_year": payment_methods[1].card.exp_year,
                "funding": payment_methods[1].card.funding,
            }
        }
    ]


def test_change_default_payment_method(api_client, standard_product_user,
        mock_stripe):
    payment_methods = [
        mock_stripe.PaymentMethod.create(standard_product_user.stripe_id),
        mock_stripe.PaymentMethod.create(standard_product_user.stripe_id)
    ]
    user_payment_methods = standard_product_user.stripe_customer.payment_methods
    assert [pm.is_default for pm in user_payment_methods] == [True, False]

    api_client.force_login(standard_product_user)
    response = api_client.patch(
        '/v1/billing/payment-methods/%s/' % payment_methods[1].id,
        data={'is_default': True}
    )
    assert response.status_code == 200
    user_payment_methods = standard_product_user.stripe_customer.payment_methods
    assert [pm.is_default for pm in user_payment_methods] == [False, True]


def test_delete_payment_method(api_client, user):
    user.stripe_id = 'cus_KUzdQUhqIjwTNh'
    user.save()
    api_client.force_login(user)
    response = api_client.delete('/v1/billing/payment-methods/')
    import json
    print(json.dumps(response.json(), indent=4))


def test_create_payment_intent(api_client, user):
    user.stripe_id = 'cus_KUzdQUhqIjwTNh'
    user.save()
    api_client.force_login(user)
    response = api_client.post('/v1/billing/payment-methods/')
    import json
    print(json.dumps(response.json(), indent=4))
