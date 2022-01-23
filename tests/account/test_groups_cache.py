from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_delete(api_client, user, budget_f,
        create_group):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = create_group(parent=account)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_create(api_client, user, budget_f,
        create_group):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    create_group(parent=account)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.post(
        "/v1/accounts/%s/groups/" % account.pk,
        data={'name': 'New Name', 'children': [subaccount.pk]}
    )
    assert response.status_code == 201

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_update(api_client, user, budget_f,
        create_group):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = create_group(parent=account)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200

    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'name': 'Test Name',
        'color': '#EFEFEF'
    })
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['name'] == 'Test Name'
    assert response.json()['data'][0]['color'] == '#EFEFEF'
