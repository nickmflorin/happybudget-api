import datetime
import pytest


@pytest.mark.freeze_time('2020-01-03')
def test_get_budget_account_subaccounts(api_client, user, create_budget_account,
        create_budget, create_budget_subaccount, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    another_account = create_budget_account(budget=budget)
    subaccounts = [
        create_budget_subaccount(
            parent=account,
            budget=budget,
            created_at=datetime.datetime(2020, 1, 1)
        ),
        create_budget_subaccount(
            parent=account,
            budget=budget,
            created_at=datetime.datetime(2020, 1, 2)
        ),
        create_budget_subaccount(parent=another_account, budget=budget)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": subaccounts[0].pk,
            "name": subaccounts[0].name,
            "identifier": "%s" % subaccounts[0].identifier,
            "description": subaccounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-03 00:00:00",
            "quantity": subaccounts[0].quantity,
            "rate": subaccounts[0].rate,
            "multiplier": subaccounts[0].multiplier,
            "type": "subaccount",
            "object_id": account.pk,
            "budget": budget.pk,
            "parent_type": "account",
            "account": account.pk,
            "actual": None,
            "estimated": None,
            "variance": None,
            "subaccounts": [],
            "fringes": [],
            "created_by": user.pk,
            "updated_by": user.pk,
            "group": None,
            "unit": {
                "id": subaccounts[0].unit,
                "name": models.BudgetSubAccount.UNITS[subaccounts[0].unit]
            },
            "ancestors": [
                {
                    "type": "budget",
                    "id": budget.pk,
                    "name": budget.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "identifier": account.identifier,
                    "description": account.description,
                }
            ],
            "siblings": [{
                "id": subaccounts[1].id,
                "type": "subaccount",
                "identifier": subaccounts[1].identifier,
                "name": subaccounts[1].name,
                "description": subaccounts[1].description,
            }],
        },
        {
            "id": subaccounts[1].pk,
            "name": subaccounts[1].name,
            "identifier": "%s" % subaccounts[1].identifier,
            "description": subaccounts[1].description,
            "created_at": "2020-01-02 00:00:00",
            "updated_at": "2020-01-03 00:00:00",
            "quantity": subaccounts[1].quantity,
            "rate": subaccounts[1].rate,
            "multiplier": subaccounts[1].multiplier,
            "type": "subaccount",
            "object_id": account.pk,
            "budget": budget.pk,
            "parent_type": "account",
            "account": account.pk,
            "actual": None,
            "estimated": None,
            "variance": None,
            "subaccounts": [],
            "fringes": [],
            "group": None,
            "created_by": user.pk,
            "updated_by": user.pk,
            "unit": {
                "id": subaccounts[1].unit,
                "name": models.BudgetSubAccount.UNITS[subaccounts[1].unit]
            },
            "ancestors": [
                {
                    "type": "budget",
                    "id": budget.pk,
                    "name": budget.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "identifier": account.identifier,
                    "description": account.description,
                }
            ],
            "siblings": [{
                "id": subaccounts[0].id,
                "type": "subaccount",
                "identifier": subaccounts[0].identifier,
                "name": subaccounts[0].name,
                "description": subaccounts[0].description,
            }],
        },
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_subaccount(api_client, user, create_budget_account,
        create_budget, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    api_client.force_login(user)
    response = api_client.post(
        "/v1/accounts/%s/subaccounts/" % account.pk,
        data={
            'name': 'New Subaccount',
            'identifier': '100',
            'description': 'Test'
        }
    )
    assert response.status_code == 201
    subaccount = models.BudgetSubAccount.objects.first()
    assert subaccount.name == "New Subaccount"
    assert subaccount.description == "Test"
    assert subaccount.identifier == "100"

    assert subaccount is not None
    assert response.json() == {
        "id": subaccount.pk,
        "name": 'New Subaccount',
        "identifier": '100',
        "description": 'Test',
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": None,
        "rate": None,
        "multiplier": None,
        "unit": None,
        "type": "subaccount",
        "object_id": account.pk,
        "budget": budget.pk,
        "parent_type": "account",
        "account": account.pk,
        "actual": None,
        "estimated": None,
        "variance": None,
        "subaccounts": [],
        "fringes": [],
        "siblings": [],
        "group": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "ancestors": [
            {
                "type": "budget",
                "id": budget.pk,
                "name": budget.name,
            },
            {
                "id": account.id,
                "type": "account",
                "identifier": account.identifier,
                "description": account.description,
            }
        ]
    }
