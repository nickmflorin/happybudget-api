from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
def test_fringes_cache_invalidated_on_delete(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    fringe = f.create_fringe(budget=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    fringe.delete()

    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_fringes_cache_invalidated_on_bulk_delete(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    fringes = [
        f.create_fringe(budget=budget),
        f.create_fringe(budget=budget),
        f.create_fringe(budget=budget)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 3

    response = api_client.patch(
        "/v1/budgets/%s/bulk-delete-fringes/" % budget.pk,
        data={'ids': [fringes[0].pk, fringes[1].pk]})
    assert response.status_code == 200

    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
def test_fringes_cache_invalidated_on_create(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    f.create_fringe(budget=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.post(
        "/v1/budgets/%s/fringes/" % budget.pk,
        data={'name': 'New Name'}
    )
    assert response.status_code == 201

    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][1]['name'] == 'New Name'


@override_settings(CACHE_ENABLED=True)
def test_fringes_cache_invalidated_on_bulk_create(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    f.create_fringe(budget=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.patch(
        "/v1/budgets/%s/bulk-create-fringes/" % budget.pk,
        format='json',
        data={'data': [{'name': 'Name 1'}, {'name': 'Name 2'}]}
    )
    assert response.status_code == 201

    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 3
    assert response.json()['data'][1]['name'] == 'Name 1'
    assert response.json()['data'][2]['name'] == 'Name 2'


@override_settings(CACHE_ENABLED=True)
def test_fringes_cache_invalidated_on_update(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    fringes = [f.create_fringe(budget=budget), f.create_fringe(budget=budget)]

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
    assert response.status_code == 200

    response = api_client.patch("/v1/fringes/%s/" % fringes[0].pk, data={
        'name': 'Test Name'
    })
    assert response.status_code == 200

    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['name'] == 'Test Name'


@override_settings(CACHE_ENABLED=True)
def test_fringes_cache_invalidated_on_bulk_update(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    fringes = [f.create_fringe(budget=budget), f.create_fringe(budget=budget)]

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-fringes/" % budget.pk,
        format='json',
        data={'data': [
            {'id': fringes[0].pk, 'name': 'Name 1'},
            {'id': fringes[1].pk, 'name': 'Name 2'}
        ]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['name'] == 'Name 1'
    assert response.json()['data'][1]['name'] == 'Name 2'
