from django.test import override_settings
import mock

from rest_framework import status
from rest_framework.response import Response

from happybudget.app.budget.views import BudgetActualsOwnersViewSet


@override_settings(CACHE_ENABLED=True)
def test_delete_actual_invalidates_caches(api_client, user, f):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    subaccount = f.create_subaccount(parent=account)
    actual = f.create_actual(budget=budget, owner=subaccount, value=100)

    api_client.force_login(user)

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100

    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.delete("/v1/actuals/%s/" % actual.pk)
    assert response.status_code == 204

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 0

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 0

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 0

    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_create_actual_invalidates_caches(api_client, user, f):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    subaccount = f.create_subaccount(parent=account)
    f.create_actual(budget=budget, owner=subaccount, value=100)

    api_client.force_login(user)

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100

    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.post(
        "/v1/budgets/%s/actuals/" % budget.pk,
        format='json',
        data={
            'value': 100.0,
            'name': 'New Actual',
            'owner': {
                'type': 'subaccount',
                'id': subaccount.pk
            }
        })

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 200

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 200

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 200

    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][1]['name'] == 'New Actual'
    assert response.json()['data'][1]['value'] == 100.0


@override_settings(CACHE_ENABLED=True)
def test_update_actual_invalidates_caches(api_client, user, f):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    subaccount = f.create_subaccount(parent=account)
    actual = f.create_actual(budget=budget, owner=subaccount, value=100)

    api_client.force_login(user)

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100

    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.patch("/v1/actuals/%s/" % actual.pk, data={
        'value': 150.0
    })

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 150

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 150

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 150

    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['value'] == 150.0


@override_settings(CACHE_ENABLED=True)
def test_bulk_update_actuals_invalidates_caches(api_client, user, f):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    subaccount = f.create_subaccount(parent=account)
    another_subaccount = f.create_subaccount(parent=account)
    actuals = [
        f.create_actual(budget=budget, value=100, owner=subaccount),
        f.create_actual(budget=budget, value=120, owner=another_subaccount)
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

    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['actual'] == 220.0

    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['actual'] == 100.0
    assert response.json()['data'][1]['actual'] == 120.0

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 220.0

    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-actuals/" % budget.pk,
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

    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['actual'] == 140.0

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 140.0

    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['value'] == 120.0
    assert response.json()['data'][1]['value'] == 20.0

    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['actual'] == 0.0
    assert response.json()['data'][1]['actual'] == 140.0


@override_settings(CACHE_ENABLED=True)
def test_bulk_create_actuals_invalidates_caches(api_client, user, f):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    subaccount = f.create_subaccount(parent=account)
    another_subaccount = f.create_subaccount(parent=account)

    f.create_actual(budget=budget, value=100, owner=subaccount)
    f.create_actual(budget=budget, value=120, owner=another_subaccount)

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

    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['actual'] == 220.0

    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['actual'] == 100.0
    assert response.json()['data'][1]['actual'] == 120.0

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 220.0

    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/budgets/%s/bulk-create-actuals/" % budget.pk,
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
    assert response.status_code == 200

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 100.0

    response = api_client.get("/v1/subaccounts/%s/" % another_subaccount.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 260.0

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 360.0

    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['actual'] == 360.0

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 360.0

    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 4
    assert response.json()['data'][0]['value'] == 100.0
    assert response.json()['data'][1]['value'] == 120.0
    assert response.json()['data'][2]['value'] == 120.0
    assert response.json()['data'][3]['value'] == 20.0

    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['actual'] == 100.0
    assert response.json()['data'][1]['actual'] == 260.0


@override_settings(CACHE_ENABLED=True)
def test_bulk_delete_actuals_invalidates_caches(api_client, user, f):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    subaccount = f.create_subaccount(parent=account)
    another_subaccount = f.create_subaccount(parent=account)

    actuals = [
        f.create_actual(budget=budget, value=100, owner=subaccount),
        f.create_actual(budget=budget, value=60, owner=subaccount),
        f.create_actual(budget=budget, value=120, owner=another_subaccount),
        f.create_actual(budget=budget, value=20, owner=another_subaccount),
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

    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['actual'] == 300.0

    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['actual'] == 160.0
    assert response.json()['data'][1]['actual'] == 140.0

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 300.0

    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 4

    response = api_client.patch(
        "/v1/budgets/%s/bulk-delete-actuals/" % budget.pk,
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

    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['actual'] == 80.0

    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['actual'] == 80.0

    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['value'] == 60.0
    assert response.json()['data'][1]['value'] == 20.0

    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['actual'] == 60.0
    assert response.json()['data'][1]['actual'] == 20.0


@override_settings(CACHE_ENABLED=True, APP_URL="https://api.happybudget.com")
def test_actuals_cache_invalidated_on_upload_attachment(api_client, user, f,
        test_uploaded_file):
    budget = f.create_budget()
    account = f.create_budget_account(parent=budget)
    subaccount = f.create_budget_subaccount(parent=account)
    actuals = [
        f.create_actual(budget=budget, value=100, owner=subaccount),
        f.create_actual(budget=budget, value=120, owner=subaccount)
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
    assert response.status_code == 201

    # Make another request to the actuals endpoint to ensure that the
    # results are not cached.
    response = api_client.get("/v1/budgets/%s/actuals/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['attachments'] == [{
        'id': 1,
        'name': 'test.jpeg',
        'extension': 'jpeg',
        'url': 'https://api.happybudget.com/media/users/1/attachments/test.jpeg'
    }]


@override_settings(CACHE_ENABLED=True)
def test_actual_owners_search_not_cached(api_client, user, f):
    budget = f.create_budget()
    f.create_markup(parent=budget)
    account = f.create_budget_account(parent=budget)
    f.create_budget_subaccount(parent=account, count=4)

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
def test_actual_owners_invalidated_on_markup_saved(api_client, user, f):
    budget = f.create_budget()
    f.create_markup(parent=budget)
    account = f.create_budget_account(parent=budget)
    f.create_budget_subaccount(parent=account, count=4)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/actual-owners/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 5

    f.create_markup(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/actual-owners/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 6


@override_settings(CACHE_ENABLED=True)
def test_actual_owners_invalidated_on_markup_deleted(api_client, user, f):
    budget = f.create_budget()
    markup = f.create_markup(parent=budget)
    account = f.create_budget_account(parent=budget)
    f.create_budget_subaccount(parent=account, count=4)

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
def test_actual_owners_invalidated_on_subaccount_saved(api_client, user, f):
    budget = f.create_budget()
    f.create_markup(parent=budget)
    account = f.create_budget_account(parent=budget)
    f.create_budget_subaccount(parent=account, count=4)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/actual-owners/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 5

    f.create_budget_subaccount(parent=account, count=1)

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/actual-owners/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 6
