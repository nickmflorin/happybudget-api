from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_delete(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['id'] == account.pk

    account.delete()
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    # Note: This is kind of a dumb test, because this will return a 404
    # regardless of whether or not the instance was removed from the cache
    # because the Http404 is raised before the .retrieve() method executes.
    assert response.status_code == 404


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_save(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['id'] == account.pk

    response = api_client.patch(
        "/v1/accounts/%s/" % account.pk,
        data={'identifier': '1000'}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['identifier'] == '1000'


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_bulk_save(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['id'] == account.pk

    response = api_client.patch(
        "/v1/%ss/%s/bulk-update-accounts/" % (budget_f.context, budget.pk),
        format='json',
        data={'data': [{'id': account.pk, 'identifier': '1000'}]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['identifier'] == '1000'


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_bulk_delete(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['id'] == account.pk

    response = api_client.patch(
        "/v1/%ss/%s/bulk-delete-accounts/" % (budget_f.context, budget.pk),
        format='json',
        data={'ids': [account.pk]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 404


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_subaccount_delete(api_client, user,
        budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    subaccounts[0].delete()
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [subaccounts[1].pk]


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_subaccount_create(api_client, user,
        budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    new_subaccount = budget_f.create_subaccount(parent=account)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [
        s.pk for s in subaccounts] + [new_subaccount.pk]
