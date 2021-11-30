from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
def test_fringes_cache_invalidated_on_delete(api_client, user, budget_f,
        create_fringe):
    budget = budget_f.create_budget()
    fringe = create_fringe(budget=budget)

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/fringes/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    fringe.delete()

    response = api_client.get(
        "/v1/%ss/%s/fringes/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_fringes_cache_invalidated_on_create(api_client, user, budget_f,
        create_fringe):
    budget = budget_f.create_budget()
    create_fringe(budget=budget)

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/fringes/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    create_fringe(budget=budget)

    response = api_client.get(
        "/v1/%ss/%s/fringes/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
def test_fringes_cache_invalidated_on_change(api_client, user, budget_f,
        create_fringe):
    budget = budget_f.create_budget()
    fringes = [create_fringe(budget=budget), create_fringe(budget=budget)]

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/fringes/" % (budget_f.context, budget.pk))
    assert response.status_code == 200

    fringes[0].name = 'Test Name'
    fringes[0].save()

    response = api_client.get(
        "/v1/%ss/%s/fringes/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['name'] == 'Test Name'
