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
    response = api_client.get(
        "/v1/%ss/%s/markups/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    markup.delete()
    response = api_client.get(
        "/v1/%ss/%s/markups/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_create(api_client, user, budget_f,
        create_markup):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    create_markup(parent=budget, accounts=accounts)

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/markups/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    create_markup(parent=budget, accounts=accounts)

    response = api_client.get(
        "/v1/%ss/%s/markups/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_change(api_client, user, budget_f,
        create_markup):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    markup = create_markup(parent=budget, accounts=accounts)

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/markups/" % (budget_f.context, budget.pk))
    assert response.status_code == 200

    markup.description = 'Test Description'
    markup.save()

    response = api_client.get(
        "/v1/%ss/%s/markups/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['description'] == 'Test Description'
