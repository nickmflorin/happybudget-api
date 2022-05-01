from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_delete(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=subaccount),
        budget_f.create_subaccount(parent=subaccount)
    ]
    markup = f.create_markup(parent=subaccount, subaccounts=subaccounts)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/markups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.delete("/v1/markups/%s/" % markup.pk)
    assert response.status_code == 204

    response = api_client.get("/v1/subaccounts/%s/markups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_bulk_delete(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=subaccount),
        budget_f.create_subaccount(parent=subaccount)
    ]
    markup = f.create_markup(parent=subaccount, subaccounts=subaccounts)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/markups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-delete-markups/" % subaccount.pk,
        data={'ids': [markup.pk]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/subaccounts/%s/markups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_create(api_client, user, budget_f, f,
        models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=subaccount),
        budget_f.create_subaccount(parent=subaccount)
    ]
    f.create_markup(parent=subaccount, subaccounts=subaccounts)

    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/markups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.post(
        "/v1/subaccounts/%s/markups/" % subaccount.pk,
        data={
            'children': [s.pk for s in subaccounts],
            'unit': models.Markup.UNITS.percent
        }
    )
    assert response.status_code == 201

    response = api_client.get("/v1/subaccounts/%s/markups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_update(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=subaccount),
        budget_f.create_subaccount(parent=subaccount)
    ]
    markup = f.create_markup(parent=subaccount, subaccounts=subaccounts)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/groups/" % subaccount.pk)
    assert response.status_code == 200

    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'description': 'Test Description'
    })
    assert response.status_code == 200

    response = api_client.get("/v1/subaccounts/%s/markups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['description'] == 'Test Description'
