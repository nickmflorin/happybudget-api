import pytest


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
            "type": "account",
            "estimated": 0.0,
            "variance": 0.0,
            "actual": 0.0,
            "subaccounts": [],
            "created_by": user.pk,
            "updated_by": user.pk
        },
        {
            "id": accounts[1].pk,
            "identifier": "%s" % accounts[1].identifier,
            "description": accounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "access": [],
            "type": "account",
            "estimated": 0.0,
            "variance": 0.0,
            "actual": 0.0,
            "subaccounts": [],
            "created_by": user.pk,
            "updated_by": user.pk
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_account(api_client, user, create_budget, models):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.post("/v1/budgets/%s/accounts/" % budget.pk, data={
        'identifier': 'new_account'
    })
    assert response.status_code == 201

    account = models.BudgetAccount.objects.first()
    assert account is not None

    assert response.json() == {
        "id": account.pk,
        "identifier": 'new_account',
        "description": None,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "type": "account",
        "estimated": 0.0,
        "variance": 0.0,
        "actual": 0.0,
        "subaccounts": [],
        "created_by": user.pk,
        "updated_by": user.pk,
    }
