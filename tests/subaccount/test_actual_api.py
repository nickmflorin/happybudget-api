import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_create_actual(api_client, user, create_budget_account, create_budget,
        create_budget_subaccount, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    sub_account = create_budget_subaccount(budget=budget, parent=account)
    api_client.force_login(user)
    # We do not have to provide the object_id and parent_type since we are
    # already creating it off of the endpoint for a specific subaccount.
    response = api_client.post("/v1/subaccounts/%s/actuals/" % sub_account.pk)
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
        "vendor": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "account": {
            "id": sub_account.pk,
            "type": "subaccount",
            "name": sub_account.name,
            "identifier": sub_account.identifier,
            "description": sub_account.description
        }
    }
    actual = models.Actual.objects.first()
    assert actual is not None
    assert actual.budget == budget
    assert actual.parent == sub_account


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount_actuals(api_client, user, create_budget_subaccount,
        create_actual, create_budget, create_budget_account):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    sub_account = create_budget_subaccount(budget=budget, parent=account)
    actuals = [
        create_actual(parent=sub_account, budget=budget),
        create_actual(parent=sub_account, budget=budget)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/actuals/" % sub_account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": actuals[0].pk,
            "description": actuals[0].description,
            "vendor": actuals[0].vendor,
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
            "account": {
                "id": sub_account.pk,
                "type": "subaccount",
                "name": sub_account.name,
                "identifier": sub_account.identifier,
                "description": sub_account.description
            }
        },
        {
            "id": actuals[1].pk,
            "description": actuals[1].description,
            "vendor": actuals[1].vendor,
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
            "account": {
                "id": sub_account.pk,
                "type": "subaccount",
                "name": sub_account.name,
                "identifier": sub_account.identifier,
                "description": sub_account.description
            }
        },
    ]
