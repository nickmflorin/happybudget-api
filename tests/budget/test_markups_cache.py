from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_delete(api_client, user, budget_f,
        create_markup):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    markup = create_markup(parent=budget, accounts=accounts)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/markups/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.delete("/v1/markups/%s/" % markup.pk)
    assert response.status_code == 204

    response = api_client.get("/v1/budgets/%s/markups/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_bulk_delete(api_client, user, budget_f,
        create_markup):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    markup = create_markup(parent=budget, accounts=accounts)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/markups/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.patch(
        "/v1/budgets/%s/bulk-delete-markups/" % budget.pk,
        data={'ids': [markup.pk]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/budgets/%s/markups/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_create(api_client, user, budget_f, models,
        create_markup):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    create_markup(parent=budget, accounts=accounts)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/markups/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.post("/v1/budgets/%s/markups/" % budget.pk, data={
        'children': [a.pk for a in accounts],
        'unit': models.Markup.UNITS.percent
    })
    assert response.status_code == 201

    response = api_client.get("/v1/budgets/%s/markups/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_update(api_client, user, budget_f,
        create_markup):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    markup = create_markup(parent=budget, accounts=accounts)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/markups/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['description'] == markup.description

    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'description': 'Test Description'
    })
    assert response.status_code == 200

    response = api_client.get("/v1/budgets/%s/markups/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['description'] == 'Test Description'
