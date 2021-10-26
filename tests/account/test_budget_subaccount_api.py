import datetime
import pytest

from greenbudget.app import signals


@pytest.mark.freeze_time('2020-01-03')
def test_get_budget_account_subaccounts(api_client, user, create_budget_account,
        create_budget, create_budget_subaccount):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        another_account = create_budget_account(parent=budget)
        subaccounts = [
            create_budget_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 1)
            ),
            create_budget_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 2)
            ),
            create_budget_subaccount(parent=another_account)
        ]
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": subaccounts[0].pk,
            "identifier": "%s" % subaccounts[0].identifier,
            "description": subaccounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-03 00:00:00",
            "quantity": subaccounts[0].quantity,
            "rate": subaccounts[0].rate,
            "multiplier": subaccounts[0].multiplier,
            "type": "subaccount",
            "object_id": account.pk,
            "parent_type": "account",
            "nominal_value": 0.0,
            "fringe_contribution": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "fringes": [],
            "created_by": user.pk,
            "updated_by": user.pk,
            "contact": None,
            "unit": None,
            "attachments": []
        },
        {
            "id": subaccounts[1].pk,
            "identifier": "%s" % subaccounts[1].identifier,
            "description": subaccounts[1].description,
            "created_at": "2020-01-02 00:00:00",
            "updated_at": "2020-01-03 00:00:00",
            "quantity": subaccounts[1].quantity,
            "rate": subaccounts[1].rate,
            "multiplier": subaccounts[1].multiplier,
            "type": "subaccount",
            "object_id": account.pk,
            "parent_type": "account",
            "nominal_value": 0.0,
            "fringe_contribution": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "fringes": [],
            "created_by": user.pk,
            "updated_by": user.pk,
            "contact": None,
            "unit": None,
            "attachments": []
        },
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_subaccount(api_client, user, create_budget_account,
        create_budget, models):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
    api_client.force_login(user)
    response = api_client.post(
         "/v1/accounts/%s/subaccounts/" % account.pk, data={
             'identifier': '100',
             'description': 'Test'
         })
    assert response.status_code == 201
    subaccount = models.BudgetSubAccount.objects.first()
    assert subaccount.description == "Test"
    assert subaccount.identifier == "100"

    assert subaccount is not None
    assert response.json() == {
        "id": subaccount.pk,
        "identifier": '100',
        "description": 'Test',
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": None,
        "rate": None,
        "multiplier": None,
        "contact": None,
        "unit": None,
        "type": "subaccount",
        "object_id": account.pk,
        "parent_type": "account",
        "nominal_value": 0.0,
        "fringe_contribution": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "fringes": [],
        "created_by": user.pk,
        "updated_by": user.pk,
        "attachments": []
    }
