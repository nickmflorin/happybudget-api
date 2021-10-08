import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_account_markups(api_client, user, models,
        create_budget_account, create_budget, create_markup):
    budget = create_budget()
    markup = create_markup(parent=budget)
    account = create_budget_account(parent=budget, markups=[markup])

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/markups/" % budget.pk)
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
        "children": [account.pk]
    }]


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_markup(api_client, user, create_budget_subaccounts,
        create_budget_account, create_budget, models):
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
    assert account.markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/markups/" % budget.pk, data={
        'identifier': 'Markup Identifier',
        'rate': 20,
        'unit': models.Markup.UNITS.flat,
        'children': [account.pk],
    })
    assert response.status_code == 201

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0

    account.refresh_from_db()
    assert account.markup_contribution == 20.0

    budget.refresh_from_db()
    assert budget.accumulated_markup_contribution == 20.0

    markup = models.Markup.objects.first()
    assert markup is not None
    assert markup.identifier == "Markup Identifier"
    assert markup.children.count() == 1
    assert markup.children.all()[0] == account
    assert markup.parent == budget

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
        "children": [account.pk]
    }

    assert response.json()["budget"]["accumulated_markup_contribution"] == 20.0
    assert response.json()["budget"]["nominal_value"] == 20.0


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_markup_no_children(api_client, user, create_budget,
        models):
    budget = create_budget()
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/markups/" % budget.pk, data={
        'identifier': 'Markup Identifier',
        'rate': 20,
        'unit': models.Markup.UNITS.flat
    })
    assert response.status_code == 400


def test_create_markup_invalid_child(api_client, user,
        create_budget_account, create_budget):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(parent=another_budget)

    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/markups/" % budget.pk, data={
        'children': [account.pk],
    })
    assert response.status_code == 400


def test_bulk_delete_budget_markups(api_client, user, create_budget, models,
        create_budget_account, create_markup):
    budget = create_budget()
    markups = [
        create_markup(parent=budget, unit=models.Markup.UNITS.flat, rate=100),
        create_markup(parent=budget, unit=models.Markup.UNITS.flat, rate=100)
    ]
    account = create_budget_account(parent=budget, markups=markups)
    assert budget.accumulated_markup_contribution == 200.0
    assert account.markup_contribution == 200.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-delete-markups/" % budget.pk,
        data={'ids': [m.pk for m in markups]}
    )

    assert response.status_code == 200
    assert models.Markup.objects.count() == 0

    budget.refresh_from_db()
    assert budget.accumulated_markup_contribution == 0.0

    account.refresh_from_db()
    assert account.markup_contribution == 0.0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Budget.
    assert response.json()['data']['id'] == budget.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert response.json()['data']['accumulated_markup_contribution'] == 0.0
    assert response.json()['data']['actual'] == 0.0
