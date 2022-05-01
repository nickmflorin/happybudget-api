from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_delete(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]
    markup = f.create_markup(parent=account, subaccounts=subaccounts)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.delete("/v1/markups/%s/" % markup.pk)
    assert response.status_code == 204

    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_bulk_delete(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]
    markup = f.create_markup(parent=account, subaccounts=subaccounts)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.patch(
        "/v1/accounts/%s/bulk-delete-markups/" % account.pk,
        data={'ids': [markup.pk]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_create(api_client, user, budget_f, models,
        f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]
    f.create_markup(parent=account, subaccounts=subaccounts)

    api_client.force_login(user)

    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.post(
        "/v1/accounts/%s/markups/" % account.pk,
        data={
            'children': [s.pk for s in subaccounts],
            'unit': models.Markup.UNITS.percent
        }
    )
    assert response.status_code == 201

    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_update(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]
    markup = f.create_markup(parent=account, subaccounts=subaccounts)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200

    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'description': 'Test Description'
    })
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['description'] == 'Test Description'
