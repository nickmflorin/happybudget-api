import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_update_actual(api_client, user, create_budget_account,
        create_budget, create_actual):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    actual = create_actual(parent=account, budget=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actual.pk,
        data={
            "vendor": "Vendor Name",
            "payment_id": "Payment ID",
            "payment_method": 1,
        }
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": actual.pk,
        "description": actual.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "purchase_order": "%s" % actual.purchase_order,
        "date": actual.date,
        "payment_id": "Payment ID",
        "value": actual.value,
        "vendor": "Vendor Name",
        "created_by": user.pk,
        "updated_by": user.pk,
        "payment_method": {
            "id": 1,
            "name": actual.PAYMENT_METHODS[1]
        },
        "account": {
            "id": account.pk,
            "type": "account",
            "identifier": account.identifier,
            "description": account.description
        }
    }
    actual.refresh_from_db()
    assert actual.payment_id == "Payment ID"
    assert actual.vendor == "Vendor Name"


@pytest.mark.freeze_time('2020-01-01')
def test_change_actual_parent(api_client, user, create_budget_account,
        create_budget, create_actual):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    another_account = create_budget_account(budget=budget)
    actual = create_actual(parent=account, budget=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actual.pk,
        data={"object_id": another_account.pk, "parent_type": "account"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": actual.pk,
        "description": actual.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "purchase_order": "%s" % actual.purchase_order,
        "date": actual.date,
        "payment_id": actual.payment_id,
        "value": actual.value,
        "vendor": actual.vendor,
        "created_by": user.pk,
        "updated_by": user.pk,
        "payment_method": {
            "id": actual.payment_method,
            "name": actual.PAYMENT_METHODS[actual.payment_method]
        },
        "account": {
            "id": another_account.pk,
            "type": "account",
            "identifier": another_account.identifier,
            "description": another_account.description
        }
    }
    actual.refresh_from_db()
    assert actual.budget == budget
    assert actual.parent == another_account


@pytest.mark.freeze_time('2020-01-01')
def test_change_actual_parent_invalid(api_client, user, create_budget_account,
        create_budget, create_actual):
    budgets = [create_budget(), create_budget()]
    account = create_budget_account(budget=budgets[0])
    another_account = create_budget_account(budget=budgets[1])
    actual = create_actual(parent=account, budget=budgets[0])

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actual.pk,
        data={"object_id": another_account.pk, "parent_type": "account"}
    )
    assert response.status_code == 400
