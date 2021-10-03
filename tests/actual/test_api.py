import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_update_actual(api_client, user, create_budget_account,
        create_budget, create_actual, create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)
    actual = create_actual(owner=subaccount, budget=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/actuals/%s/" % actual.pk, data={
        "payment_id": "Payment ID",
        "payment_method": 1,
    })

    assert response.status_code == 200
    assert response.json() == {
        "id": actual.pk,
        "type": "actual",
        "description": actual.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "purchase_order": "%s" % actual.purchase_order,
        "date": actual.date,
        "payment_id": "Payment ID",
        "value": actual.value,
        "contact": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "payment_method": {
            "id": 1,
            "name": actual.PAYMENT_METHODS[1]
        },
        "owner": {
            "id": subaccount.pk,
            "type": "subaccount",
            "identifier": subaccount.identifier,
            "description": subaccount.description,
        }
    }
    actual.refresh_from_db()
    assert actual.payment_id == "Payment ID"
    assert actual.payment_method == 1


@pytest.mark.freeze_time('2020-01-01')
def test_change_actual_parent_to_subaccount(api_client, user, create_budget,
        create_budget_account, create_actual, create_budget_subaccount,
        create_markup):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    markup = create_markup(parent=account)
    subaccount = create_budget_subaccount(parent=account, markups=[markup])
    actuals = [
        create_actual(owner=markup, budget=budget, value=100.0),
        create_actual(owner=markup, budget=budget, value=50.0)
    ]

    markup.refresh_from_db()
    assert markup.actual == 150.0

    subaccount.refresh_from_db()
    assert subaccount.actual == 150.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actuals[0].pk,
        format="json",
        data={"owner": {
            "id": subaccount.pk,
            "type": "subaccount"
        }}
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": actuals[0].pk,
        "type": "actual",
        "description": actuals[0].description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "purchase_order": "%s" % actuals[0].purchase_order,
        "date": actuals[0].date,
        "payment_id": actuals[0].payment_id,
        "value": actuals[0].value,
        "contact": actuals[0].contact,
        "created_by": user.pk,
        "updated_by": user.pk,
        "payment_method": {
            "id": actuals[0].payment_method,
            "name": actuals[0].PAYMENT_METHODS[actuals[0].payment_method]
        },
        "owner": {
            "id": subaccount.pk,
            "type": "subaccount",
            "identifier": subaccount.identifier,
            "description": subaccount.description
        }
    }
    # The sub account will still have an actual value of 150.0 because it still
    # has a sum of 150.0 across the actuals of it's children (actual child or
    # markup child).
    subaccount.refresh_from_db()
    assert subaccount.actual == 150.0

    account.refresh_from_db()
    assert account.actual == 150.0

    markup.refresh_from_db()
    assert markup.actual == 50.0

    actuals[0].refresh_from_db()
    assert actuals[0].budget == budget
    assert actuals[0].owner == subaccount


@pytest.mark.freeze_time('2020-01-01')
def test_change_actual_parent_to_markup(api_client, user, create_budget,
        create_budget_account, create_actual, create_budget_subaccount,
        create_markup):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    markup = create_markup(parent=account)
    subaccount = create_budget_subaccount(parent=account, markups=[markup])
    actuals = [
        create_actual(owner=subaccount, budget=budget, value=100.0),
        create_actual(owner=subaccount, budget=budget, value=50.0)
    ]

    markup.refresh_from_db()
    assert markup.actual == 0.0

    subaccount.refresh_from_db()
    assert subaccount.actual == 150.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actuals[0].pk,
        format="json",
        data={"owner": {
            "id": markup.pk,
            "type": "markup"
        }}
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": actuals[0].pk,
        "type": "actual",
        "description": actuals[0].description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "purchase_order": "%s" % actuals[0].purchase_order,
        "date": actuals[0].date,
        "payment_id": actuals[0].payment_id,
        "value": actuals[0].value,
        "contact": actuals[0].contact,
        "created_by": user.pk,
        "updated_by": user.pk,
        "payment_method": {
            "id": actuals[0].payment_method,
            "name": actuals[0].PAYMENT_METHODS[actuals[0].payment_method]
        },
        "owner": {
            "id": markup.pk,
            "type": "markup",
            "identifier": markup.identifier,
            "description": markup.description,
        }
    }
    # The sub account will still have an actual value of 150.0 because it still
    # has a sum of 150.0 across the actuals of it's children (actual child or
    # markup child).
    subaccount.refresh_from_db()
    assert subaccount.actual == 150.0

    account.refresh_from_db()
    assert account.actual == 150.0

    markup.refresh_from_db()
    assert markup.actual == 100.0

    actuals[0].refresh_from_db()
    assert actuals[0].budget == budget
    assert actuals[0].owner == markup


def test_change_actual_owner_invalid_subaccount(api_client, user, create_actual,
        create_budget_account, create_budget, create_budget_subaccount):
    budgets = [create_budget(), create_budget()]
    account = create_budget_account(parent=budgets[0])
    subaccount = create_budget_subaccount(parent=account)
    another_account = create_budget_account(parent=budgets[1])
    another_subaccount = create_budget_subaccount(parent=another_account)
    actual = create_actual(owner=subaccount, budget=budgets[0])

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actual.pk,
        format="json",
        data={"owner": {"type": "subaccount", "id": another_subaccount.pk}}
    )
    assert response.status_code == 400


def test_change_actual_owner_invalid_markup(api_client, user, create_actual,
        create_budget_account, create_budget, create_budget_subaccount,
        create_markup):
    budgets = [create_budget(), create_budget()]

    account = create_budget_account(parent=budgets[0])
    subaccount = create_budget_subaccount(parent=account)

    another_account = create_budget_account(parent=budgets[1])
    another_subaccount = create_budget_subaccount(parent=another_account)
    markup = create_markup(parent=another_subaccount)

    actual = create_actual(owner=subaccount, budget=budgets[0])

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actual.pk,
        format="json",
        data={"owner": {"type": "markup", "id": markup.pk}}
    )
    assert response.status_code == 400
