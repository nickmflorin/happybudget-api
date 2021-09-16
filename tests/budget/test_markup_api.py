import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_account_markups(api_client, user, models,
        create_budget_account, create_budget, create_budget_account_markup):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    markup = create_budget_account_markup(parent=budget, children=[account])

    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/markups/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
        "id": markup.pk,
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
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
def test_create_budget_account_markup(api_client, user, create_budget_account,
        create_budget, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)

    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/markups/" % budget.pk, data={
        'identifier': 'Markup Identifier',
        'children': [account.pk],
    })
    assert response.status_code == 201

    markup = models.BudgetAccountMarkup.objects.first()
    assert markup is not None
    assert markup.identifier == 'Markup Identifier'
    assert markup.children.count() == 1
    assert markup.children.first() == account
    assert markup.parent == budget

    assert response.json() == {
        "id": markup.pk,
        "identifier": 'Markup Identifier',
        "description": markup.description,
        "rate": markup.rate,
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


def test_create_budget_account_markup_invalid_child(api_client, user,
        create_budget_account, create_budget):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(budget=another_budget)

    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/markups/" % budget.pk, data={
        'children': [account.pk],
    })
    assert response.status_code == 400
