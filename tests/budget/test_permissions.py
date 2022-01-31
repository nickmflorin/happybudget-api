import pytest


def test_get_budget_not_logged_in(api_client, create_budget):
    budget = create_budget()
    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 401


def test_get_budgets_not_logged_in(api_client):
    response = api_client.get("/v1/budgets/")
    assert response.status_code == 401


def test_get_budgets_with_share_token(api_client, create_budget,
        create_share_token):
    budget = create_budget()
    share_token = create_share_token(instance=budget)
    api_client.include_share_token(share_token)
    response = api_client.get("/v1/budgets/")
    assert response.status_code == 401


def test_get_budget_accounts_not_logged_in(api_client, budget_f):
    budget = budget_f.create_budget()
    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 401


def test_get_shared_budget_accounts(api_client, create_budget,
        create_share_token):
    budget = create_budget()
    share_token = create_share_token(instance=budget)
    api_client.include_share_token(share_token)
    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200


@pytest.mark.freeze_time('2020-01-01')
def test_get_another_shared_budget_accounts(api_client, create_budget,
        create_share_token):
    budget = create_budget()
    another_budget = create_budget()
    share_token = create_share_token(instance=budget)
    api_client.include_share_token(share_token)
    response = api_client.get("/v1/budgets/%s/children/" % another_budget.pk)
    assert response.status_code == 401


def test_get_template_accounts_with_share_token(api_client, create_template,
        create_share_token):
    budget = create_template()
    share_token = create_share_token(instance=budget)
    api_client.include_share_token(share_token)
    response = api_client.get("/v1/templates/%s/children/" % budget.pk)
    assert response.status_code == 401


def test_get_another_user_budget(api_client, budget_f, user, admin_user):
    budget = budget_f.create_budget(created_by=admin_user)
    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_get_shared_budget(api_client, create_budget, create_share_token):
    budget = create_budget()
    share_token = create_share_token(instance=budget)
    api_client.include_share_token(share_token)
    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "budget",
        "image": None
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_another_shared_budget(api_client, create_budget,
        create_share_token):
    budget = create_budget()
    another_budget = create_budget()
    share_token = create_share_token(instance=budget)
    api_client.include_share_token(share_token)
    response = api_client.get("/v1/budgets/%s/" % another_budget.pk)
    assert response.status_code == 401


def test_update_shared_budget(api_client, create_budget, create_share_token):
    budget = create_budget()
    share_token = create_share_token(instance=budget)
    api_client.include_share_token(share_token)
    response = api_client.post("/v1/budgets/%s/" % budget.pk, data={
        'name': 'New Name'
    })
    assert response.status_code == 401


def test_create_budget_not_logged_in(api_client):
    response = api_client.post("/v1/budgets/", data={'name': 'New Name'})
    assert response.status_code == 401


def test_create_budget_with_share_token(api_client, create_share_token,
        create_budget):
    budget = create_budget()
    share_token = create_share_token(instance=budget)
    api_client.include_share_token(share_token)
    response = api_client.post("/v1/budgets/", data={'name': 'New Name'})
    assert response.status_code == 401


def test_get_permissioned_budget(api_client, user, create_budget):
    budgets = [create_budget(), create_budget()]
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/" % budgets[1].pk)
    assert response.status_code == 403
    assert response.json() == {'errors': [{
        'message': (
            'The user does not have the correct subscription to view this '
            'budget.'
        ),
        'code': 'product_permission_error',
        'error_type': 'permission',
        'products': '__any__',
        'permission_id': 'multiple_budgets'
    }]}


def test_create_additional_budget_unsubscribed(api_client, user, create_budget):
    create_budget()
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/", data={"name": "Test Name"})
    assert response.status_code == 403
    assert response.json() == {'errors': [{
        'message': "The user's subscription does not support multiple budgets.",
        'code': 'product_permission_error',
        'error_type': 'permission',
        'products': '__any__',
        'permission_id': 'multiple_budgets'
    }]}


def test_duplicate_budget_unsubscribed(api_client, user, create_budget):
    original = create_budget(created_by=user)
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/duplicate/" % original.pk)
    assert response.status_code == 403
    assert response.json() == {'errors': [{
        'message': "The user's subscription does not support multiple budgets.",
        'code': 'product_permission_error',
        'error_type': 'permission',
        'products': '__any__',
        'permission_id': 'multiple_budgets'
    }]}
