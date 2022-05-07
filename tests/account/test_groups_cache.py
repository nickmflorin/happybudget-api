from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_delete(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=account, group=group),
        budget_f.create_subaccount(parent=account)
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [subaccounts[0].pk]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [subaccounts[0].pk]

    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 404


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_create(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)

    api_client.force_login(user)

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0

    response = api_client.post(
        "/v1/accounts/%s/groups/" % account.pk,
        data={'name': 'Group', 'children': [subaccount.pk]}
    )
    assert response.status_code == 201

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [subaccount.pk]


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_update(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=account, group=group),
        budget_f.create_subaccount(parent=account)
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [subaccounts[0].pk]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [subaccounts[0].pk]

    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'name': 'New Name',
        'children': [s.pk for s in subaccounts]
    })
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['name'] == 'New Name'
    assert response.json()['data'][0]['children'] == [s.pk for s in subaccounts]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['name'] == 'New Name'
    assert response.json()['children'] == [s.pk for s in subaccounts]


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_create_child(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=account, group=group),
        budget_f.create_subaccount(parent=account, group=group)
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [s.pk for s in subaccounts]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    response = api_client.post(
        "/v1/accounts/%s/children/" % account.pk,
        data={'group': group.pk}
    )
    assert response.status_code == 201
    created_id = response.json()['id']

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [
        s.pk for s in subaccounts] + [created_id]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [
        s.pk for s in subaccounts] + [created_id]


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_bulk_create_children(api_client, user,
        budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=account, group=group),
        budget_f.create_subaccount(parent=account, group=group)
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [s.pk for s in subaccounts]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-children/" % account.pk,
        format='json',
        data={'data': [{'group': group.pk}]}
    )
    assert response.status_code == 200
    created_id = response.json()['children'][0]['id']

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [
        s.pk for s in subaccounts] + [created_id]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [
        s.pk for s in subaccounts] + [created_id]


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_update_child(api_client, user, budget_f,
        f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=account, group=group),
        budget_f.create_subaccount(parent=account, group=group)
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [s.pk for s in subaccounts]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    response = api_client.patch(
        "/v1/subaccounts/%s/" % subaccounts[0].pk,
        format='json',
        data={'group': None}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [subaccounts[1].pk]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [subaccounts[1].pk]


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_bulk_update_child(api_client, user,
        budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=account, group=group),
        budget_f.create_subaccount(parent=account, group=group)
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [s.pk for s in subaccounts]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    response = api_client.patch(
        "/v1/accounts/%s/bulk-update-children/" % account.pk,
        format='json',
        data={'data': [{'id': subaccounts[0].pk, 'group': None}]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [subaccounts[1].pk]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [subaccounts[1].pk]


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_delete_child(api_client, user, budget_f,
        f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=account, group=group),
        budget_f.create_subaccount(parent=account, group=group)
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [s.pk for s in subaccounts]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    response = api_client.delete("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert response.status_code == 204

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [subaccounts[1].pk]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [subaccounts[1].pk]


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_bulk_delete_child(api_client, user,
        budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=account, group=group),
        budget_f.create_subaccount(parent=account, group=group)
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [s.pk for s in subaccounts]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    response = api_client.patch(
        "/v1/accounts/%s/bulk-delete-children/" % account.pk,
        data={'ids': [subaccounts[0].pk]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['children'] == [subaccounts[1].pk]

    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [subaccounts[1].pk]
