from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
def test_accounts_cache_on_search(api_client, user, budget_f):
    budget = budget_f.create_budget()
    # These accounts should not be cached in the response because we will
    # be including a search query parameter.
    budget_f.create_account(parent=budget, identifier='Jack')
    budget_f.create_account(parent=budget, identifier='Jill')

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/accounts/" % (budget_f.context, budget.pk))
    assert response.status_code == 200

    response = api_client.get(
        "/v1/%ss/%s/accounts/?search=jill"
        % (budget_f.context, budget.pk)
    )
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
def test_accounts_cache_invalidated_on_delete(api_client, user, budget_f):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/accounts/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2

    accounts[0].delete()
    response = api_client.get(
        "/v1/%ss/%s/accounts/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
def test_accounts_cache_invalidated_on_create(api_client, user, budget_f):
    budget = budget_f.create_budget()
    budget_f.create_account(parent=budget)
    budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/accounts/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2

    budget_f.create_account(parent=budget)
    response = api_client.get(
        "/v1/%ss/%s/accounts/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 3


@override_settings(CACHE_ENABLED=True)
def test_accounts_cache_invalidated_on_change(api_client, user, budget_f):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/accounts/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2

    accounts[0].description = 'Test Description'
    accounts[0].save()

    response = api_client.get(
        "/v1/%ss/%s/accounts/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['description'] == 'Test Description'
