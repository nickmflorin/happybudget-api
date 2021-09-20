import pytest

from greenbudget.app import signals


@pytest.mark.freeze_time('2020-01-01')
def test_create_actual(api_client, user, create_budget_account, create_budget,
        create_budget_subaccount, models):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(budget=budget)
        subaccount = create_budget_subaccount(parent=account)
    api_client.force_login(user)
    # We do not have to provide the object_id and parent_type since we are
    # already creating it off of the endpoint for a specific subaccount.
    response = api_client.post("/v1/subaccounts/%s/actuals/" % subaccount.pk)
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
def test_get_subaccount_actuals(api_client, user, create_budget_subaccount,
        create_actual, create_budget, create_budget_account):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(budget=budget)
        subaccount = create_budget_subaccount(parent=account)
        actuals = [
            create_actual(subaccount=subaccount, budget=budget),
            create_actual(subaccount=subaccount, budget=budget)
        ]
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/actuals/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": actuals[0].pk,
            "description": actuals[0].description,
            "contact": actuals[0].contact,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "purchase_order": "%s" % actuals[0].purchase_order,
            "date": actuals[0].date,
            "payment_id": actuals[0].payment_id,
            "value": actuals[0].value,
            "created_by": user.pk,
            "updated_by": user.pk,
            "payment_method": {
                "id": actuals[0].payment_method,
                "name": actuals[0].PAYMENT_METHODS[actuals[0].payment_method]
            },
            "subaccount": {
                "id": subaccount.pk,
                "type": "subaccount",
                "identifier": subaccount.identifier,
                "description": subaccount.description
            }
        },
        {
            "id": actuals[1].pk,
            "description": actuals[1].description,
            "contact": actuals[1].contact,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "purchase_order": "%s" % actuals[1].purchase_order,
            "date": actuals[1].date,
            "payment_id": actuals[1].payment_id,
            "value": actuals[1].value,
            "created_by": user.pk,
            "updated_by": user.pk,
            "payment_method": {
                "id": actuals[1].payment_method,
                "name": actuals[1].PAYMENT_METHODS[actuals[1].payment_method]
            },
            "subaccount": {
                "id": subaccount.pk,
                "type": "subaccount",
                "identifier": subaccount.identifier,
                "description": subaccount.description
            }
        },
    ]
