import pytest
from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_detail_cache_invalidated_on_delete(api_client, user, context,
        create_context_budget):
    budget = create_context_budget(context=context)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['id'] == budget.pk

    budget.delete()
    response = api_client.get("/v1/%ss/%s/" % (context, budget.pk))
    # Note: This is kind of a dumb test, because this will return a 404
    # regardless of whether or not the instance was removed from the cache
    # because the Http404 is raised before the .retrieve() method executes.
    assert response.status_code == 404


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_detail_cache_invalidated_on_save(api_client, user, context,
        create_context_budget):
    budget = create_context_budget(context=context)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['id'] == budget.pk

    budget.name = 'New Name'
    budget.save()

    response = api_client.get("/v1/%ss/%s/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['name'] == 'New Name'


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_accounts_cache_on_search(api_client, user, context, create_account,
        create_context_budget):
    budget = create_context_budget(context=context)
    # These accounts should not be cached in the response because we will
    # be including a search query parameter.
    create_account(parent=budget, context=context, identifier='Jack'),
    create_account(parent=budget, context=context, identifier='Jill')

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/accounts/" % (context, budget.pk))
    assert response.status_code == 200

    response = api_client.get(
        "/v1/%ss/%s/accounts/?search=jill"
        % (context, budget.pk)
    )
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_accounts_cache_invalidated_on_delete(api_client, user, context,
        create_account, create_context_budget):
    budget = create_context_budget(context=context)
    accounts = [
        create_account(parent=budget, context=context),
        create_account(parent=budget, context=context)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/accounts/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2

    accounts[0].delete()
    response = api_client.get("/v1/%ss/%s/accounts/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_accounts_cache_invalidated_on_create(api_client, user, context,
        create_account, create_context_budget):
    budget = create_context_budget(context=context)
    create_account(parent=budget, context=context)
    create_account(parent=budget, context=context)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/accounts/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2

    create_account(parent=budget, context=context)
    response = api_client.get("/v1/%ss/%s/accounts/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 3


@pytest.mark.freeze_time('2020-01-01')
@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_accounts_cache_invalidated_on_change(api_client, user, context,
        create_account, create_context_budget):
    budget = create_context_budget(context=context)
    accounts = [
        create_account(parent=budget, context=context),
        create_account(parent=budget, context=context)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/accounts/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2

    accounts[0].description = 'Test Description'
    accounts[0].save()

    response = api_client.get("/v1/%ss/%s/accounts/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['description'] == 'Test Description'


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_groups_cache_invalidated_on_delete(api_client, user, context,
        create_context_budget, create_group):
    budget = create_context_budget(context=context)
    group = create_group(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/groups/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    group.delete()
    response = api_client.get("/v1/%ss/%s/groups/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_groups_cache_invalidated_on_create(api_client, user, context,
        create_context_budget, create_group):
    budget = create_context_budget(context=context)
    create_group(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/groups/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    create_group(parent=budget)
    response = api_client.get("/v1/%ss/%s/groups/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_groups_cache_invalidated_on_change(api_client, user, context,
        create_context_budget, create_group):
    budget = create_context_budget(context=context)
    group = create_group(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/groups/" % (context, budget.pk))
    assert response.status_code == 200

    group.name = 'Test Name'
    group.save()

    response = api_client.get("/v1/%ss/%s/groups/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['name'] == 'Test Name'


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_markups_cache_invalidated_on_delete(api_client, user, context,
        create_account, create_context_budget, create_markup):
    budget = create_context_budget(context=context)
    accounts = [
        create_account(parent=budget, context=context),
        create_account(parent=budget, context=context)
    ]
    markup = create_markup(parent=budget, accounts=accounts)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/markups/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    markup.delete()
    response = api_client.get("/v1/%ss/%s/markups/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_markups_cache_invalidated_on_create(api_client, user, context,
        create_account, create_context_budget, create_markup):
    budget = create_context_budget(context=context)
    accounts = [
        create_account(parent=budget, context=context),
        create_account(parent=budget, context=context)
    ]
    create_markup(parent=budget, accounts=accounts)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/markups/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    create_markup(parent=budget, accounts=accounts)
    response = api_client.get("/v1/%ss/%s/markups/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_markups_cache_invalidated_on_change(api_client, user, context,
        create_account, create_context_budget, create_markup):
    budget = create_context_budget(context=context)
    accounts = [
        create_account(parent=budget, context=context),
        create_account(parent=budget, context=context)
    ]
    markup = create_markup(parent=budget, accounts=accounts)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/markups/" % (context, budget.pk))
    assert response.status_code == 200

    markup.description = 'Test Description'
    markup.save()

    response = api_client.get("/v1/%ss/%s/markups/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['description'] == 'Test Description'


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_fringes_cache_invalidated_on_delete(api_client, user, context,
        create_context_budget, create_fringe):
    budget = create_context_budget(context=context)
    fringe = create_fringe(budget=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/fringes/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    fringe.delete()
    response = api_client.get("/v1/%ss/%s/fringes/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_fringes_cache_invalidated_on_create(api_client, user, context,
        create_context_budget, create_fringe):
    budget = create_context_budget(context=context)
    create_fringe(budget=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/fringes/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    create_fringe(budget=budget)
    response = api_client.get("/v1/%ss/%s/fringes/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2


@pytest.mark.freeze_time('2020-01-01')
@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_fringes_cache_invalidated_on_change(api_client, user, context,
        create_context_budget, create_fringe):
    budget = create_context_budget(context=context)
    fringes = [create_fringe(budget=budget), create_fringe(budget=budget)]

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/fringes/" % (context, budget.pk))
    assert response.status_code == 200

    fringes[0].name = 'Test Name'
    fringes[0].save()

    response = api_client.get("/v1/%ss/%s/fringes/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['name'] == 'Test Name'


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget'])
def test_actuals_cache_invalidated_on_delete(api_client, user, context,
        create_context_budget, create_actual):
    budget = create_context_budget(context=context)
    actual = create_actual(budget=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/actuals/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    actual.delete()
    response = api_client.get("/v1/%ss/%s/actuals/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget'])
def test_actuals_cache_invalidated_on_create(api_client, user, context,
        create_context_budget, create_actual):
    budget = create_context_budget(context=context)
    create_actual(budget=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/actuals/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    create_actual(budget=budget)
    response = api_client.get("/v1/%ss/%s/actuals/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2


@pytest.mark.freeze_time('2020-01-01')
@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget'])
def test_actuals_cache_invalidated_on_change(api_client, user, context,
        create_context_budget, create_actual, create_account,
        create_subaccount):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    actuals = [
        create_actual(budget=budget, value=100, owner=subaccount),
        create_actual(budget=budget, value=120, owner=subaccount)
    ]
    assert budget.actual == 220.0

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/actuals/" % (context, budget.pk))
    assert response.status_code == 200

    actuals[0].value = 150.0
    actuals[0].save()
    budget.refresh_from_db()
    assert budget.actual == 270.0

    response = api_client.get("/v1/%ss/%s/actuals/" % (context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['value'] == 150.0
