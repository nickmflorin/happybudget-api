import pytest

from greenbudget.app import signals


@pytest.mark.freeze_time('2020-01-01')
def test_create_actual(api_client, user, create_budget_account,
        create_budget, create_budget_subaccount, models):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(budget=budget)
        subaccount = create_budget_subaccount(parent=account, budget=budget)

    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/actuals/" % budget.pk, data={
        'subaccount': subaccount.pk,
    })
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "description": None,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "purchase_order": None,
        "date": None,
        "payment_id": None,
        "value": None,
        "payment_method": None,
        "contact": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "subaccount": {
            "id": subaccount.pk,
            "type": "subaccount",
            "identifier": subaccount.identifier,
            "description": subaccount.description
        }
    }
    actual = models.Actual.objects.first()
    assert actual is not None
    assert actual.budget == budget
    assert actual.subaccount == subaccount


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_budget_actuals(api_client, user, create_budget,
        create_budget_account, create_budget_subaccount, models):
    budget = create_budget()
    accounts = [
        create_budget_account(budget=budget),
        create_budget_account(budget=budget)
    ]
    # Do not disable the signals, because disabling the signals will prevent
    # the metrics on the SubAccount(s) (and thus the Account(s) and Budget) from
    # being calculated.
    subaccounts = [
        create_budget_subaccount(
            budget=budget,
            parent=accounts[0],
            quantity=1,
            rate=100,
            multiplier=1
        ),
        create_budget_subaccount(
            budget=budget,
            parent=accounts[1],
            quantity=2,
            rate=50,
            multiplier=2
        )
    ]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-create-actuals/" % budget.pk,
        format='json',
        data={'data': [
            {'value': 40.0, 'subaccount': subaccounts[0].pk},
            {'value': 30.0, 'subaccount': subaccounts[0].pk},
            {'value': 160.0, 'subaccount': subaccounts[1].pk},
            {'value': 10.0, 'subaccount': subaccounts[1].pk},
        ]})

    assert response.status_code == 201

    # The children in the response will be the created Actuals.
    assert len(response.json()['children']) == 4
    assert response.json()['children'][0]['value'] == 40.0
    assert response.json()['children'][0]['subaccount']['id'] == subaccounts[0].pk  # noqa

    assert response.json()['children'][1]['value'] == 30.0
    assert response.json()['children'][1]['subaccount']['id'] == subaccounts[0].pk  # noqa

    assert response.json()['children'][2]['value'] == 160.0
    assert response.json()['children'][2]['subaccount']['id'] == subaccounts[1].pk  # noqa

    assert response.json()['children'][3]['value'] == 10.0
    assert response.json()['children'][3]['subaccount']['id'] == subaccounts[1].pk  # noqa

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Budget.
    assert response.json()['data']['id'] == budget.pk
    assert response.json()['data']['estimated'] == 300.0
    assert response.json()['data']['variance'] == 60.0
    assert response.json()['data']['actual'] == 240.0

    # Make sure the actual Actual(s) were created in the database.
    actuals = models.Actual.objects.all()
    assert len(actuals) == 4
    assert actuals[0].value == 40.0
    assert actuals[0].subaccount == subaccounts[0]
    assert actuals[0].created_by == user
    assert actuals[0].updated_by == user
    assert actuals[0].budget == budget
    assert actuals[1].value == 30.0
    assert actuals[1].subaccount == subaccounts[0]
    assert actuals[1].created_by == user
    assert actuals[1].updated_by == user
    assert actuals[1].budget == budget
    assert actuals[2].value == 160.0
    assert actuals[2].subaccount == subaccounts[1]
    assert actuals[2].created_by == user
    assert actuals[2].updated_by == user
    assert actuals[2].budget == budget
    assert actuals[3].value == 10.0
    assert actuals[3].subaccount == subaccounts[1]
    assert actuals[3].created_by == user
    assert actuals[3].updated_by == user
    assert actuals[3].budget == budget

    # Make sure the actual SubAccount(s) were updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].estimated == 100.0
    assert subaccounts[0].variance == 30.0
    assert subaccounts[0].actual == 70.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].estimated == 200.0
    assert subaccounts[1].variance == 30.0
    assert subaccounts[1].actual == 170.0

    # Make sure the actual Account(s) were updated in the database.
    accounts[0].refresh_from_db()
    assert accounts[0].estimated == 100.0
    assert accounts[0].variance == 30.0
    assert accounts[0].actual == 70.0

    accounts[1].refresh_from_db()
    assert accounts[1].estimated == 200.0
    assert accounts[1].variance == 30.0
    assert accounts[1].actual == 170.0

    # Make sure the Budget was updated in the database.
    budget.refresh_from_db()
    assert budget.estimated == 300.0
    assert budget.variance == 60.0
    assert budget.actual == 240.0


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_actuals(api_client, user, create_budget,
        create_budget_account, create_budget_subaccount, create_actual):
    budget = create_budget()
    accounts = [
        create_budget_account(budget=budget),
        create_budget_account(budget=budget)
    ]
    # Do not disable the signals, because disabling the signals will prevent
    # the metrics on the SubAccount(s) (and thus the Account(s) and Budget) from
    # being calculated.
    subaccounts = [
        create_budget_subaccount(
            budget=budget,
            parent=accounts[0],
            quantity=1,
            rate=100,
            multiplier=1
        ),
        create_budget_subaccount(
            budget=budget,
            parent=accounts[1],
            quantity=2,
            rate=50,
            multiplier=2
        )
    ]
    actuals = [
        create_actual(
            subaccount=subaccounts[0],
            budget=budget,
            value=40.0
        ),
        create_actual(
            subaccount=subaccounts[0],
            budget=budget,
            value=30.0
        ),
        create_actual(
            subaccount=subaccounts[1],
            budget=budget,
            value=160.0
        ),
        create_actual(
            subaccount=subaccounts[1],
            budget=budget,
            value=10.0
        )
    ]
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].estimated == 100.0
    assert subaccounts[0].variance == 30.0
    assert subaccounts[0].actual == 70.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].estimated == 200.0
    assert subaccounts[1].variance == 30.0
    assert subaccounts[1].actual == 170.0

    accounts[0].refresh_from_db()
    assert accounts[0].estimated == 100.0
    assert accounts[0].variance == 30.0
    assert accounts[0].actual == 70.0

    accounts[1].refresh_from_db()
    assert accounts[1].estimated == 200.0
    assert accounts[1].variance == 30.0
    assert accounts[1].actual == 170.0

    budget.refresh_from_db()
    assert budget.estimated == 300.0
    assert budget.variance == 60.0
    assert budget.actual == 240.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-actuals/" % budget.pk,
        format='json',
        data={'data': [
            {'id': actuals[0].pk, 'value': 30.0},
            {'id': actuals[1].pk, 'value': 20.0},
            {'id': actuals[2].pk, 'value': 150.0},
            {'id': actuals[3].pk, 'value': 0.0},
        ]})

    assert response.status_code == 200

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Budget.
    assert response.json()['data']['id'] == budget.pk
    assert response.json()['data']['estimated'] == 300.0
    assert response.json()['data']['variance'] == 100.0
    assert response.json()['data']['actual'] == 200.0

    # Make sure the actual Actual(s) were updated in the database.
    actuals[0].refresh_from_db()
    assert actuals[0].value == 30.0
    actuals[1].refresh_from_db()
    assert actuals[1].value == 20.0
    actuals[2].refresh_from_db()
    assert actuals[2].value == 150.0
    actuals[3].refresh_from_db()
    assert actuals[3].value == 0.0

    # Make sure the actual SubAccount(s) were updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].estimated == 100.0
    assert subaccounts[0].variance == 50.0
    assert subaccounts[0].actual == 50.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].estimated == 200.0
    assert subaccounts[1].variance == 50.0
    assert subaccounts[1].actual == 150.0

    # Make sure the actual Account(s) were updated in the database.
    accounts[0].refresh_from_db()
    assert accounts[0].estimated == 100.0
    assert accounts[0].variance == 50.0
    assert accounts[0].actual == 50.0

    accounts[1].refresh_from_db()
    assert accounts[1].estimated == 200.0
    assert accounts[1].variance == 50.0
    assert accounts[1].actual == 150.0

    # Make sure the Budget was updated in the database.
    budget.refresh_from_db()
    assert budget.estimated == 300.0
    assert budget.variance == 100.0
    assert budget.actual == 200.0


def test_bulk_delete_actuals(api_client, user, create_budget, create_actual,
        models, create_budget_account, create_budget_subaccount):
    budget = create_budget()
    accounts = [
        create_budget_account(budget=budget),
        create_budget_account(budget=budget)
    ]
    # Do not disable the signals, because disabling the signals will prevent
    # the metrics on the SubAccount(s) (and thus the Account(s) and Budget) from
    # being calculated.
    subaccounts = [
        create_budget_subaccount(
            budget=budget,
            parent=accounts[0],
            quantity=1,
            rate=100,
            multiplier=1
        ),
        create_budget_subaccount(
            budget=budget,
            parent=accounts[1],
            quantity=2,
            rate=50,
            multiplier=2
        )
    ]
    actuals = [
        create_actual(
            subaccount=subaccounts[0],
            budget=budget,
            value=40.0
        ),
        create_actual(
            subaccount=subaccounts[0],
            budget=budget,
            value=30.0
        ),
        create_actual(
            subaccount=subaccounts[1],
            budget=budget,
            value=160.0
        ),
        create_actual(
            subaccount=subaccounts[1],
            budget=budget,
            value=10.0
        )
    ]
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].estimated == 100.0
    assert subaccounts[0].variance == 30.0
    assert subaccounts[0].actual == 70.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].estimated == 200.0
    assert subaccounts[1].variance == 30.0
    assert subaccounts[1].actual == 170.0

    accounts[0].refresh_from_db()
    assert accounts[0].estimated == 100.0
    assert accounts[0].variance == 30.0
    assert accounts[0].actual == 70.0

    accounts[1].refresh_from_db()
    assert accounts[1].estimated == 200.0
    assert accounts[1].variance == 30.0
    assert accounts[1].actual == 170.0

    budget.refresh_from_db()
    assert budget.estimated == 300.0
    assert budget.variance == 60.0
    assert budget.actual == 240.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-delete-actuals/" % budget.pk, data={
            'ids': [actuals[0].pk, actuals[1].pk, actuals[3].pk]
        })
    assert response.status_code == 200

    # Make sure the Actual(s) were deleted in the database.
    assert models.Actual.objects.count() == 1

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Budget.
    assert response.json()['data']['id'] == budget.pk
    assert response.json()['data']['estimated'] == 300.0
    assert response.json()['data']['variance'] == 140.0
    assert response.json()['data']['actual'] == 160.0

    # Make sure the actual SubAccount(s) were updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].estimated == 100.0
    assert subaccounts[0].variance == 100.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].estimated == 200.0
    assert subaccounts[1].variance == 40.0
    assert subaccounts[1].actual == 160.0

    # Make sure the actual Account(s) were updated in the database.
    accounts[0].refresh_from_db()
    assert accounts[0].estimated == 100.0
    assert accounts[0].variance == 100.0
    assert accounts[0].actual == 0.0

    accounts[1].refresh_from_db()
    assert accounts[1].estimated == 200.0
    assert accounts[1].variance == 40.0
    assert accounts[1].actual == 160.0

    # Make sure the Budget was updated in the database.
    budget.refresh_from_db()
    assert budget.estimated == 300.0
    assert budget.variance == 140.0
    assert budget.actual == 160.0
