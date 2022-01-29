import datetime
from datetime import timezone

from greenbudget.app.budgeting.managers import BudgetingPolymorphicRowManager


def test_get_account(api_client, user, budget_f):
    api_client.force_login(user)
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    table_siblings = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": account.pk,
        "identifier": "%s" % account.identifier,
        "description": account.description,
        "type": "account",
        "domain": budget_f.context,
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "table": [
            {
                'id': account.pk,
                'identifier': account.identifier,
                'type': 'account',
                'description': account.description,
                'domain': budget_f.context,
            },
            {
                'id': table_siblings[0].pk,
                'identifier': table_siblings[0].identifier,
                'type': 'account',
                'description': table_siblings[0].description,
                'domain': budget_f.context,
            },
            {
                'id': table_siblings[1].pk,
                'identifier': table_siblings[1].identifier,
                'type': 'account',
                'description': table_siblings[1].description,
                'domain': budget_f.context,
            }
        ],
        "order": "n",
        "ancestors": [{
            "type": "budget",
            "domain": budget_f.context,
            "id": budget.pk,
            "name": budget.name
        }]
    }


def test_get_permissioned_account(api_client, user, budget_df):
    budgets = [budget_df.create_budget(), budget_df.create_budget()]
    account = budget_df.create_account(parent=budgets[1])
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 403
    assert response.json() == {'errors': [{
        'message': (
            'The user does not have the correct subscription to view this '
            'account.'
        ),
        'code': 'product_permission_error',
        'error_type': 'permission',
        'products': '__any__',
        'permission_id': 'multiple_budgets'
    }]}


def test_update_account(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(
        parent=budget,
        identifier="original_identifier"
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % account.pk, data={
        'identifier': 'new_account',
        'description': 'Account description'
    })
    assert response.status_code == 200
    assert response.json()["id"] == account.pk
    assert response.json()["identifier"] == "new_account"
    assert response.json()["description"] == "Account description"
    assert response.json()["ancestors"] == [{
        "type": "budget",
        "domain": budget_f.context,
        "id": budget.pk,
        "name": budget.name
    }]
    account.refresh_from_db()
    assert account.identifier == "new_account"
    assert account.description == "Account description"


def test_bulk_update_subaccounts(api_client, user, freezer, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 1)
        ),
        budget_f.create_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 2)
        )
    ]
    api_client.force_login(user)
    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/accounts/%s/bulk-update-children/" % account.pk,
        format='json',
        data={'data': [
            {
                'id': subaccounts[0].pk,
                'multiplier': 2,
                'quantity': 2,
                'rate': 5
            },
            {
                'id': subaccounts[1].pk,
                'multiplier': 2,
                'quantity': 2,
                'rate': 5
            }
        ]})
    assert response.status_code == 200

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Account.
    assert response.json()['data']['id'] == account.pk
    assert response.json()['data']['nominal_value'] == 40.0
    assert response.json()['data']['actual'] == 0.0
    assert len(response.json()['data']['children']) == 2
    assert response.json()['data']['children'][0] == subaccounts[0].pk
    assert response.json()['data']['children'][1] == subaccounts[1].pk

    assert response.json()['budget']['id'] == budget.pk
    assert response.json()['budget']['nominal_value'] == 40.0
    assert response.json()['budget']['actual'] == 0.0

    # Make sure the SubAccount(s) are updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].multiplier == 2
    assert subaccounts[0].quantity == 2
    assert subaccounts[0].rate == 5

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].multiplier == 2
    assert subaccounts[1].quantity == 2
    assert subaccounts[1].rate == 5

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 40.0
    assert account.actual == 0.0

    # Make sure the Budget is updated in the database.
    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)
    assert budget.nominal_value == 40.0
    assert budget.actual == 0.0


def test_bulk_update_subaccount_fringes(api_client, user, create_fringe,
        budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 1),
            quantity=1,
            rate=100,
            multiplier=1
        ),
        budget_f.create_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 2),
            quantity=1,
            rate=100,
            multiplier=1
        )
    ]
    fringes = [
        create_fringe(budget=budget, rate=0.5),
        create_fringe(budget=budget, rate=0.2)
    ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-update-children/" % account.pk,
        format='json',
        data={
            'data': [{
                'id': subaccounts[0].pk,
                'fringes': [f.pk for f in fringes]
            }]
        })

    assert response.status_code == 200

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Account.
    assert response.json()['data']['id'] == account.pk
    assert response.json()['data']['nominal_value'] == 200.0
    assert response.json()['data']['accumulated_fringe_contribution'] == 70.0
    assert response.json()['data']['actual'] == 0.0
    assert len(response.json()['data']['children']) == 2
    assert response.json()['data']['children'][0] == subaccounts[0].pk
    assert response.json()['data']['children'][1] == subaccounts[1].pk

    assert response.json()['budget']['id'] == budget.pk
    assert response.json()['budget']['nominal_value'] == 200.0
    assert response.json()['budget']['accumulated_fringe_contribution'] == 70.0

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 200.0
    assert account.accumulated_fringe_contribution == 70.0
    assert account.actual == 0.0

    # Make sure the SubAccount(s) are updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100
    assert subaccounts[0].fringe_contribution == 70.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 100
    assert subaccounts[1].fringe_contribution == 0

    # Make sure the Budget is updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 200.0
    assert budget.accumulated_fringe_contribution == 70.0


def test_bulk_delete_subaccounts(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(
            parent=account,
            quantity=1,
            rate=100,
            multiplier=1
        ),
        budget_f.create_subaccount(
            parent=account,
            quantity=1,
            rate=100,
            multiplier=1
        )
    ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-delete-children/" % account.pk,
        data={'ids': [sub.pk for sub in subaccounts]}
    )
    assert response.status_code == 200
    assert models.SubAccount.objects.count() == 0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Account.
    assert response.json()['data']['id'] == account.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert response.json()['data']['actual'] == 0.0
    assert len(response.json()['data']['children']) == 0

    assert response.json()['budget']['id'] == budget.pk
    assert response.json()['budget']['nominal_value'] == 0.0
    assert response.json()['budget']['actual'] == 0.0

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 0.0
    assert account.actual == 0.0

    # Make sure the Budget is updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 0.0


def test_bulk_update_subaccounts_budget_updated_once(api_client, user, budget_f,
        monkeypatch):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 1)
        ),
        budget_f.create_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 2)
        )
    ]
    api_client.force_login(user)

    calls = []
    monkeypatch.setattr(
        BudgetingPolymorphicRowManager,
        'mark_budgets_updated',
        lambda obj, instances: calls.append(None)
    )
    response = api_client.patch(
        "/v1/accounts/%s/bulk-update-children/" % account.pk,
        format='json',
        data={
            'data': [
                {
                    'id': subaccounts[0].pk,
                    'name': 'New Desc 1',
                },
                {
                    'id': subaccounts[1].pk,
                    'name': 'New Desc 2',
                }
            ]
        })
    assert response.status_code == 200
    assert len(calls) == 1


def test_bulk_create_subaccounts(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-children/" % account.pk,
        format='json',
        data={'data': [
            {
                'multiplier': 2,
                'quantity': 2,
                'rate': 5
            },
            {
                'multiplier': 2,
                'quantity': 2,
                'rate': 5
            }
        ]})
    assert response.status_code == 201
    subaccounts = models.SubAccount.objects.all()
    assert len(subaccounts) == 2

    assert len(response.json()['children']) == 2
    assert response.json()['children'][0]['id'] == subaccounts[0].pk
    assert response.json()['children'][0]['nominal_value'] == 20.0
    assert response.json()['children'][0]['actual'] == 0.0
    assert response.json()['children'][1]['id'] == subaccounts[1].pk
    assert response.json()['children'][1]['nominal_value'] == 20.0
    assert response.json()['children'][1]['actual'] == 0.0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Account.
    assert response.json()['data']['id'] == account.pk
    assert response.json()['data']['nominal_value'] == 40.0
    assert response.json()['data']['actual'] == 0.0
    assert len(response.json()['data']['children']) == 2
    assert response.json()['data']['children'][0] == subaccounts[0].pk
    assert response.json()['data']['children'][1] == subaccounts[1].pk

    assert response.json()['budget']['id'] == budget.pk
    assert response.json()['budget']['nominal_value'] == 40.0
    assert response.json()['budget']['actual'] == 0.0

    # Make sure the SubAccount(s) are updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].multiplier == 2
    assert subaccounts[0].quantity == 2
    assert subaccounts[0].rate == 5

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].multiplier == 2
    assert subaccounts[1].quantity == 2
    assert subaccounts[1].rate == 5

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 40.0
    assert account.actual == 0.0

    # Make sure the Budget is updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 40.0
    assert budget.actual == 0.0
