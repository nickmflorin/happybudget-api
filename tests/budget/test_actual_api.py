import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_create_actual(api_client, user, create_budget_account,
        create_budget, create_budget_subaccount, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)

    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/actuals/" % budget.pk, data={
        'subaccount': subaccount.pk,
    })
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
        "subaccount": {
            "id": subaccount.pk,
            "type": "subaccount",
            "identifier": subaccount.identifier,
            "description": subaccount.description,
            "name": subaccount.name,
        }
    }
    actual = models.Actual.objects.first()
    assert actual is not None
    assert actual.budget == budget
    assert actual.subaccount == subaccount


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_budget_actuals(api_client, user, create_budget,
        create_budget_account, create_budget_subaccount, models):
    api_client.force_login(user)
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)

    response = api_client.patch(
        "/v1/budgets/%s/bulk-create-actuals/" % budget.pk,
        format='json',
        data={'data': [
            {
                'description': 'New Description 1',
                'subaccount': subaccount.pk

            },
            {
                'description': 'New Description 2',
                'subaccount': subaccount.pk

            },
        ]})
    assert response.status_code == 201

    actuals = models.Actual.objects.all()
    assert len(actuals) == 2
    assert actuals[0].description == "New Description 1"
    assert actuals[0].subaccount == subaccount
    assert actuals[0].created_by == user
    assert actuals[0].updated_by == user
    assert actuals[0].budget == budget
    assert actuals[1].description == "New Description 2"
    assert actuals[1].subaccount == subaccount
    assert actuals[1].created_by == user
    assert actuals[1].updated_by == user
    assert actuals[1].budget == budget

    assert response.json()['data'][0]['description'] == 'New Description 1'
    assert response.json()['data'][1]['description'] == 'New Description 2'


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_actuals(api_client, user, create_budget,
        create_budget_account, create_budget_subaccount, create_actual):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)
    actuals = [
        create_actual(subaccount=subaccount, budget=budget),
        create_actual(subaccount=subaccount, budget=budget)
    ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-actuals/" % budget.pk,
        format='json',
        data={
            'data': [
                {
                    'id': actuals[0].pk,
                    'description': 'New Description 1',
                },
                {
                    'id': actuals[1].pk,
                    'description': 'New Description 2',
                }
            ]
        })
    assert response.status_code == 200

    actuals[0].refresh_from_db()
    assert actuals[0].description == "New Description 1"
    actuals[1].refresh_from_db()
    assert actuals[1].description == "New Description 2"


def test_bulk_delete_actuals(api_client, user, create_budget, models,
        create_budget_account, create_budget_subaccount, create_actual):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)
    actuals = [
        create_actual(subaccount=subaccount, budget=budget),
        create_actual(subaccount=subaccount, budget=budget)
    ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-delete-actuals/" % budget.pk, data={
            'ids': [a.pk for a in actuals]
        })
    assert response.status_code == 200
    assert models.Actual.objects.count() == 0
