import pytest

from greenbudget.app.account.models import BudgetAccount


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_accounts(api_client, user, create_budget_account,
        create_budget):
    api_client.force_login(user)
    budget = create_budget()
    accounts = [
        create_budget_account(budget=budget),
        create_budget_account(budget=budget)
    ]
    response = api_client.get("/v1/budgets/%s/accounts/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": accounts[0].pk,
            "identifier": "%s" % accounts[0].identifier,
            "description": accounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "access": [],
            "budget": budget.pk,
            "type": "account",
            "estimated": None,
            "variance": None,
            "actual": None,
            "subaccounts": [],
            "group": None,
            "created_by": user.pk,
            "updated_by": user.pk,
            "ancestors": [{
                "type": "budget",
                "id": budget.pk,
                "name": budget.name,
            }],
            "siblings": [{
                "type": "account",
                "id": accounts[1].pk,
                "identifier": accounts[1].identifier,
                "description": accounts[1].description
            }]
        },
        {
            "id": accounts[1].pk,
            "identifier": "%s" % accounts[1].identifier,
            "description": accounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "access": [],
            "budget": budget.pk,
            "type": "account",
            "estimated": None,
            "variance": None,
            "actual": None,
            "subaccounts": [],
            "group": None,
            "created_by": user.pk,
            "updated_by": user.pk,
            "ancestors": [{
                "type": "budget",
                "id": budget.pk,
                "name": budget.name
            }],
            "siblings": [{
                "type": "account",
                "id": accounts[0].pk,
                "identifier": accounts[0].identifier,
                "description": accounts[0].description
            }]
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_account(api_client, user, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.post("/v1/budgets/%s/accounts/" % budget.pk, data={
        'identifier': 'new_account'
    })
    assert response.status_code == 201

    account = BudgetAccount.objects.first()
    assert account is not None

    assert response.json() == {
        "id": account.pk,
        "identifier": 'new_account',
        "description": None,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "budget": budget.pk,
        "type": "account",
        "estimated": None,
        "variance": None,
        "actual": None,
        "subaccounts": [],
        "group": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "ancestors": [{
            "type": "budget",
            "id": budget.pk,
            "name": budget.name
        }],
        "siblings": []
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_account_duplicate_number(api_client, user, create_budget,
        create_budget_account):
    api_client.force_login(user)
    budget = create_budget()
    create_budget_account(budget=budget, identifier="new_account")
    response = api_client.post("/v1/budgets/%s/accounts/" % budget.pk, data={
        'identifier': 'new_account'
    })
    assert response.status_code == 400
