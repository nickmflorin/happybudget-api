import pytest

from greenbudget.app import signals


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_account_subaccount_markups(api_client, user, models,
        create_budget_subaccount, create_budget_account, create_budget,
        create_budget_subaccount_markup):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(budget=budget)
        subaccount = create_budget_subaccount(
            parent=account,
            budget=budget,
        )
        markup = create_budget_subaccount_markup(
            parent=account,
            children=[subaccount]
        )

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
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
def test_create_budget_account_subaccount_markup(api_client, user,
        create_budget_subaccount, create_budget_account, create_budget,
        models):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(budget=budget)
        subaccount = create_budget_subaccount(parent=account, budget=budget)

    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/markups/" % account.pk, data={
        'identifier': 'Markup Identifier',
        'children': [subaccount.pk],
    })
    assert response.status_code == 201

    markup = models.BudgetSubAccountMarkup.objects.first()
    assert markup is not None
    assert markup.identifier == "Markup Identifier"
    assert markup.children.count() == 1
    assert markup.children.first() == subaccount
    assert markup.parent == account

    assert response.json() == {
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
    }


def test_create_budget_account_subaccount_markup_invalid_child(api_client, user,
        create_budget_subaccount, create_budget_account, create_budget):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(budget=budget)
        another_account = create_budget_account(budget=budget)
        subaccount = create_budget_subaccount(
            parent=another_account, budget=budget)

    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/markups/" % account.pk, data={
        'children': [subaccount.pk],
    })
    assert response.status_code == 400
