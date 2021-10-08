import pytest

from greenbudget.app import signals


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_account_subaccount_markups(api_client, user, models,
        create_budget_account, create_budget, create_markup,
        create_budget_subaccount):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        markup = create_markup(parent=account)
        subaccounts = [
            create_budget_subaccount(parent=account, markups=[markup]),
            create_budget_subaccount(parent=account, markups=[markup])
        ]

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    assert response.json()['data'] == [{
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "actual": 0.0,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [sub.pk for sub in subaccounts]
    }]


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_account_subaccount_markup(api_client, user,
        create_budget_subaccounts, create_budget_account, create_budget,
        models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccounts = create_budget_subaccounts(
        parent=account,
        quantity=1,
        rate=10,
        count=2
    )

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.accumulated_markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/markups/" % account.pk, data={
        'identifier': 'Markup Identifier',
        'rate': 20,
        'unit': models.Markup.UNITS.flat,
        'children': [s.pk for s in subaccounts],
    })
    assert response.status_code == 201

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 20.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 20.0

    account.refresh_from_db()
    assert account.accumulated_markup_contribution == 40.0

    budget.refresh_from_db()
    assert budget.accumulated_markup_contribution == 40.0

    markup = models.Markup.objects.first()
    assert markup is not None
    assert markup.identifier == "Markup Identifier"
    assert markup.children.count() == 2
    assert markup.children.all()[0] == subaccounts[0]
    assert markup.children.all()[1] == subaccounts[1]
    assert markup.parent == account

    assert response.json()["data"] == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "actual": 0.0,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [s.pk for s in subaccounts]
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 40.0
    assert response.json()["parent"]["nominal_value"] == 20.0

    assert response.json()["budget"]["accumulated_markup_contribution"] == 40.0
    assert response.json()["budget"]["nominal_value"] == 20.0


def test_create_budget_account_subaccount_markup_invalid_child(api_client, user,
        create_budget_subaccount, create_budget_account, create_budget):
    with signals.disable():
        budget = create_budget()
        another_budget = create_budget()
        account = create_budget_account(parent=budget)
        another_account = create_budget_account(parent=another_budget)
        subaccount = create_budget_subaccount(parent=another_account)

    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/markups/" % account.pk, data={
        'children': [subaccount.pk],
    })
    assert response.status_code == 400


def test_bulk_delete_account_markups(api_client, user, create_budget, models,
        create_budget_account, create_markup, create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    markups = [
        create_markup(parent=account, unit=models.Markup.UNITS.flat, rate=100),
        create_markup(parent=account, unit=models.Markup.UNITS.flat, rate=100)
    ]
    subaccount = create_budget_subaccount(parent=account, markups=markups)

    assert budget.accumulated_markup_contribution == 200.0
    assert account.accumulated_markup_contribution == 200.0
    assert subaccount.markup_contribution == 200.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-delete-markups/" % account.pk,
        data={'ids': [m.pk for m in markups]}
    )

    assert response.status_code == 200
    assert models.Markup.objects.count() == 0

    budget.refresh_from_db()
    assert budget.accumulated_markup_contribution == 0.0

    account.refresh_from_db()
    assert account.accumulated_markup_contribution == 0.0

    subaccount.refresh_from_db()
    assert subaccount.markup_contribution == 0.0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Account.
    assert response.json()['data']['id'] == account.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert response.json()['data']['accumulated_markup_contribution'] == 0.0
    assert response.json()['data']['actual'] == 0.0

    assert response.json()['budget']['id'] == budget.pk
    assert response.json()['budget']['nominal_value'] == 0.0
    assert response.json()['budget']['accumulated_markup_contribution'] == 0.0
    assert response.json()['budget']['actual'] == 0.0
