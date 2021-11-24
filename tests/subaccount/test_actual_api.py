import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_create_actual(api_client, user, budget_df, models):
    budget = budget_df.create_budget()
    account = budget_df.create_account(parent=budget)
    subaccount = budget_df.create_subaccount(parent=account)
    api_client.force_login(user)
    # We do not have to provide the object_id and parent_type since we are
    # already creating it off of the endpoint for a specific subaccount.
    response = api_client.post("/v1/subaccounts/%s/actuals/" % subaccount.pk)

    actual = models.Actual.objects.first()
    assert actual is not None

    assert response.status_code == 201
    assert response.json() == {
        "id": actual.pk,
        "type": "actual",
        "name": None,
        "notes": None,
        "purchase_order": None,
        "date": None,
        "payment_id": None,
        "value": None,
        "actual_type": None,
        "contact": None,
        "attachments": [],
        "order": "n",
        "owner": {
            "id": subaccount.pk,
            "type": "subaccount",
            "identifier": subaccount.identifier,
            "description": subaccount.description
        }
    }
    assert actual.budget == budget
    assert actual.owner == subaccount


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount_actuals(api_client, user, create_actual, budget_df):
    budget = budget_df.create_budget()
    account = budget_df.create_account(parent=budget)
    subaccount = budget_df.create_subaccount(parent=account)
    actuals = [
        create_actual(owner=subaccount, budget=budget),
        create_actual(owner=subaccount, budget=budget)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/actuals/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": actuals[0].pk,
            "type": "actual",
            "name": actuals[0].name,
            "notes": actuals[0].notes,
            "contact": actuals[0].contact,
            "purchase_order": "%s" % actuals[0].purchase_order,
            "date": actuals[0].date,
            "payment_id": actuals[0].payment_id,
            "value": actuals[0].value,
            "actual_type": None,
            "attachments": [],
            "order": "n",
            "owner": {
                "id": subaccount.pk,
                "type": "subaccount",
                "identifier": subaccount.identifier,
                "description": subaccount.description
            }
        },
        {
            "id": actuals[1].pk,
            "type": "actual",
            "name": actuals[1].name,
            "notes": actuals[1].notes,
            "contact": actuals[1].contact,
            "purchase_order": "%s" % actuals[1].purchase_order,
            "date": actuals[1].date,
            "payment_id": actuals[1].payment_id,
            "value": actuals[1].value,
            "actual_type": None,
            "attachments": [],
            "order": "t",
            "owner": {
                "id": subaccount.pk,
                "type": "subaccount",
                "identifier": subaccount.identifier,
                "description": subaccount.description
            }
        },
    ]
