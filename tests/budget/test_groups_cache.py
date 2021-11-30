from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_delete(api_client, user, budget_f,
        create_group):
    budget = budget_f.create_budget()
    group = create_group(parent=budget)

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/groups/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    group.delete()

    response = api_client.get(
        "/v1/%ss/%s/groups/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_create(api_client, user, budget_f,
        create_group):
    budget = budget_f.create_budget()
    create_group(parent=budget)

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/groups/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    create_group(parent=budget)

    response = api_client.get(
        "/v1/%ss/%s/groups/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_change(api_client, user, budget_f,
        create_group):
    budget = budget_f.create_budget()
    group = create_group(parent=budget)

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/groups/" % (budget_f.context, budget.pk))
    assert response.status_code == 200

    group.name = 'Test Name'
    group.save()

    response = api_client.get(
        "/v1/%ss/%s/groups/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['name'] == 'Test Name'
