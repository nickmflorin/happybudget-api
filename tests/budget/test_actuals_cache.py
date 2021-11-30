from django.test import override_settings
import mock

from rest_framework import status
from rest_framework.response import Response

from greenbudget.app.budget.views import BudgetActualsOwnersViewSet


@override_settings(CACHE_ENABLED=True)
def test_actuals_cache_invalidated_on_delete(api_client, user, budget_df,
        create_actual):
    budget = budget_df.create_budget()
    actual = create_actual(budget=budget)

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.delete("/v1/actuals/%s/" % actual.pk)
    assert response.status_code == 204

    response = api_client.get(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_actuals_cache_invalidated_on_create(api_client, user, budget_df,
        create_actual):
    budget = budget_df.create_budget()
    create_actual(budget=budget)

    api_client.force_login(user)

    response = api_client.get(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.post(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk), data={
            'value': 100.0,
            'name': 'New Actual'
        })

    response = api_client.get(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk))

    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][1]['name'] == 'New Actual'
    assert response.json()['data'][1]['value'] == 100.0


@override_settings(CACHE_ENABLED=True)
def test_actuals_cache_invalidated_on_change(api_client, user, budget_df,
        create_actual):
    budget = budget_df.create_budget()
    account = budget_df.create_account(parent=budget)
    subaccount = budget_df.create_subaccount(parent=account)
    actuals = [
        create_actual(budget=budget, value=100, owner=subaccount),
        create_actual(budget=budget, value=120, owner=subaccount)
    ]
    assert budget.actual == 220.0

    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 220.0

    response = api_client.get(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk))
    assert response.status_code == 200

    response = api_client.patch("/v1/actuals/%s/" % actuals[0].pk, data={
        'value': 150.0
    })
    assert response.status_code == 200

    response = api_client.get(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['value'] == 150.0
    assert response.json()['data'][1]['value'] == 120.0

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 270.0


@override_settings(CACHE_ENABLED=True)
def test_bulk_update_actuals_invalidates_caches(api_client, user, budget_df,
        create_actual):
    budget = budget_df.create_budget()
    account = budget_df.create_account(parent=budget)
    subaccount = budget_df.create_subaccount(parent=account)
    another_subaccount = budget_df.create_subaccount(parent=account)
    actuals = [
        create_actual(budget=budget, value=100, owner=subaccount),
        create_actual(budget=budget, value=120, owner=another_subaccount)
    ]
    assert budget.actual == 220.0

    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100.0

    response = api_client.get("/v1/subaccounts/%s/" % another_subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 120.0

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 220.0

    response = api_client.get("/v1/budgets/%s/accounts/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['actual'] == 220.0

    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['actual'] == 100.0
    assert response.json()['data'][1]['actual'] == 120.0

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 220.0

    response = api_client.get(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/%ss/%s/bulk-update-actuals/" % (budget_df.context, budget.pk),
        format='json',
        data={'data': [
            {'id': actuals[0].pk, 'value': 120.0, 'owner': {
                'id': another_subaccount.pk,
                'type': 'subaccount'
            }},
            {'id': actuals[1].pk, 'value': 20.0}
        ]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 0.0

    response = api_client.get("/v1/subaccounts/%s/" % another_subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 140.0

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 140.0

    response = api_client.get("/v1/budgets/%s/accounts/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['actual'] == 140.0

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 140.0

    response = api_client.get(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['value'] == 120.0
    assert response.json()['data'][1]['value'] == 20.0

    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['actual'] == 0.0
    assert response.json()['data'][1]['actual'] == 140.0


@override_settings(CACHE_ENABLED=True)
def test_bulk_create_actuals_invalidates_caches(api_client, user, budget_df,
        create_actual):
    budget = budget_df.create_budget()
    account = budget_df.create_account(parent=budget)
    subaccount = budget_df.create_subaccount(parent=account)
    another_subaccount = budget_df.create_subaccount(parent=account)

    create_actual(budget=budget, value=100, owner=subaccount)
    create_actual(budget=budget, value=120, owner=another_subaccount)

    assert budget.actual == 220.0

    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100.0

    response = api_client.get("/v1/subaccounts/%s/" % another_subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 120.0

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 220.0

    response = api_client.get("/v1/budgets/%s/accounts/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['actual'] == 220.0

    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['actual'] == 100.0
    assert response.json()['data'][1]['actual'] == 120.0

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 220.0

    response = api_client.get(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/%ss/%s/bulk-create-actuals/" % (budget_df.context, budget.pk),
        format='json',
        data={'data': [
            {'value': 120.0, 'owner': {
                'id': another_subaccount.pk,
                'type': 'subaccount'
            }},
            {'value': 20.0, 'owner': {
                'id': another_subaccount.pk,
                'type': 'subaccount'
            }}
        ]}
    )
    assert response.status_code == 201

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100.0

    response = api_client.get("/v1/subaccounts/%s/" % another_subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 260.0

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 360.0

    response = api_client.get("/v1/budgets/%s/accounts/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['actual'] == 360.0

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 360.0

    response = api_client.get(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 4
    assert response.json()['data'][0]['value'] == 100.0
    assert response.json()['data'][1]['value'] == 120.0
    assert response.json()['data'][2]['value'] == 120.0
    assert response.json()['data'][3]['value'] == 20.0

    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['actual'] == 100.0
    assert response.json()['data'][1]['actual'] == 260.0


@override_settings(CACHE_ENABLED=True)
def test_bulk_delete_actuals_invalidates_caches(api_client, user, budget_df,
        create_actual):
    budget = budget_df.create_budget()
    account = budget_df.create_account(parent=budget)
    subaccount = budget_df.create_subaccount(parent=account)
    another_subaccount = budget_df.create_subaccount(parent=account)

    actuals = [
        create_actual(budget=budget, value=100, owner=subaccount),
        create_actual(budget=budget, value=60, owner=subaccount),
        create_actual(budget=budget, value=120, owner=another_subaccount),
        create_actual(budget=budget, value=20, owner=another_subaccount),
    ]

    assert budget.actual == 300.0

    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 160.0

    response = api_client.get("/v1/subaccounts/%s/" % another_subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 140.0

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 300.0

    response = api_client.get("/v1/budgets/%s/accounts/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['actual'] == 300.0

    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['actual'] == 160.0
    assert response.json()['data'][1]['actual'] == 140.0

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 300.0

    response = api_client.get(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 4

    response = api_client.patch(
        "/v1/%ss/%s/bulk-delete-actuals/" % (budget_df.context, budget.pk),
        format='json',
        data={'ids': [actuals[0].pk, actuals[2].pk]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 60.0

    response = api_client.get("/v1/subaccounts/%s/" % another_subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 20.0

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 80.0

    response = api_client.get("/v1/budgets/%s/accounts/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['actual'] == 80.0

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 80.0

    response = api_client.get(
        "/v1/%ss/%s/actuals/" % (budget_df.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['value'] == 60.0
    assert response.json()['data'][1]['value'] == 20.0

    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['actual'] == 60.0
    assert response.json()['data'][1]['actual'] == 20.0


@override_settings(CACHE_ENABLED=True, APP_URL="https://api.greenbudget.com")
def test_actuals_cache_invalidated_on_upload_attachment(api_client, user,
        create_budget_account, create_budget, test_uploaded_file, create_actual,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)
    actuals = [
        create_actual(budget=budget, value=100, owner=subaccount),
        create_actual(budget=budget, value=120, owner=subaccount)
    ]

    uploaded_file = test_uploaded_file('test.jpeg')

    api_client.force_login(user)

    # Make the first request to the actuals endpoint to cache the results.
    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    # Upload the attachment
    response = api_client.post(
        "/v1/actuals/%s/attachments/" % actuals[0].pk,
        data={'file': uploaded_file}
    )
    assert response.status_code == 200

    # Make another request to the actuals endpoint to ensure that the
    # results are not cached.
    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['attachments'] == [{
        'id': 1,
        'name': 'test.jpeg',
        'extension': 'jpeg',
        'url': 'https://api.greenbudget.com/media/users/1/attachments/test.jpeg'
    }]


@override_settings(CACHE_ENABLED=True)
def test_actual_owners_search_not_cached(api_client, user, create_budget,
        create_markup, create_budget_account, create_budget_subaccounts):
    budget = create_budget()
    create_markup(parent=budget)
    account = create_budget_account(parent=budget)
    create_budget_subaccounts(parent=account, count=4)

    def mock_response(*args, **kwargs):
        return Response(status=status.HTTP_200_OK)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/actual-owners/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 5

    # Make sure that adding query parameters does not use previously established
    # cached response.
    with mock.patch.object(
            BudgetActualsOwnersViewSet, 'list', wraps=mock_response) as m:
        response = api_client.get(
            "/v1/budgets/%s/actual-owners/?search=jack" % budget.pk)
    assert response.status_code == 200
    assert m.called


@override_settings(CACHE_ENABLED=True)
def test_actual_owners_invalidated_on_markup_saved(api_client, user,
        create_budget, create_markup, create_budget_account,
        create_budget_subaccounts):
    budget = create_budget()
    create_markup(parent=budget)
    account = create_budget_account(parent=budget)
    create_budget_subaccounts(parent=account, count=4)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/actual-owners/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 5

    create_markup(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/actual-owners/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 6


@override_settings(CACHE_ENABLED=True)
def test_actual_owners_invalidated_on_markup_deleted(api_client, user,
        create_budget, create_markup, create_budget_account,
        create_budget_subaccounts):
    budget = create_budget()
    markup = create_markup(parent=budget)
    account = create_budget_account(parent=budget)
    create_budget_subaccounts(parent=account, count=4)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/actual-owners/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 5

    markup.delete()

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/actual-owners/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 4


@override_settings(CACHE_ENABLED=True)
def test_actual_owners_invalidated_on_subaccount_saved(api_client, user,
        create_budget, create_markup, create_budget_account,
        create_budget_subaccounts):
    budget = create_budget()
    create_markup(parent=budget)
    account = create_budget_account(parent=budget)
    create_budget_subaccounts(parent=account, count=4)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/actual-owners/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 5

    create_budget_subaccounts(parent=account, count=1)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/actual-owners/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 6