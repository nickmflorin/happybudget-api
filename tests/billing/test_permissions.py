
def test_budget_count_product_user_has_permission(api_client, create_budget,
        standard_product_user):
    create_budget(created_by=standard_product_user)
    create_budget(created_by=standard_product_user)

    api_client.force_login(standard_product_user)
    response = api_client.post("/v1/budgets/", data={
        "name": "Test Name",
        "production_type": 1,
    })
    assert response.status_code == 201


def test_budget_count_product_user_missing_permission(api_client, create_budget,
        user):
    create_budget(created_by=user)
    create_budget(created_by=user)

    api_client.force_login(user)
    response = api_client.post("/v1/budgets/", data={
        "name": "Test Name",
        "production_type": 1,
    })
    assert response.status_code == 403
    assert response.json() == {
        'user_id': user.pk,
        'errors': [{
            'message': 'Your account is not subscribed to the correct product.',
            'code': 'product_permission_denied',
            'error_type': 'billing'
        }]
    }
