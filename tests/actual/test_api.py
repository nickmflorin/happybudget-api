import datetime

from django.test import override_settings
import pytest


def test_type_properly_serializes(api_client, user, f):
    budget = f.create_budget()
    actual_type = f.create_actual_type()
    actual = f.create_actual(budget=budget, actual_type=actual_type)

    api_client.force_login(user)
    response = api_client.get("/v1/actuals/%s/" % actual.pk)
    assert response.status_code == 200
    assert response.json()['actual_type'] == {
        'id': actual_type.pk,
        'title': actual_type.title,
        'plural_title': actual_type.plural_title,
        'order': actual_type.order,
        'color': actual_type.color.code,
    }


def test_update_actual_type(api_client, user, f):
    budget = f.create_budget()
    actual_type = f.create_actual_type()
    actual = f.create_actual(budget=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/actuals/%s/" % actual.pk, data={
        "actual_type": actual_type.pk
    })
    assert response.status_code == 200
    actual.refresh_from_db()
    assert response.json()['actual_type'] == {
        'id': actual_type.pk,
        'title': actual_type.title,
        'plural_title': actual_type.plural_title,
        'order': actual_type.order,
        'color': actual_type.color.code
    }
    assert actual.actual_type == actual_type


def test_update_actual(api_client, user, f):
    budget = f.create_budget()
    account = f.create_budget_account(parent=budget)
    subaccount = f.create_budget_subaccount(parent=account)
    actual = f.create_actual(owner=subaccount, budget=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/actuals/%s/" % actual.pk, data={
        "payment_id": "Payment ID",
    })

    assert response.status_code == 200
    assert response.json() == {
        "id": actual.pk,
        "type": "actual",
        "name": actual.name,
        "notes": actual.notes,
        "purchase_order": "%s" % actual.purchase_order,
        "date": actual.date,
        "payment_id": "Payment ID",
        "value": actual.value,
        "contact": None,
        "actual_type": None,
        "attachments": [],
        "order": "n",
        "owner": {
            "id": subaccount.pk,
            "type": "subaccount",
            "identifier": subaccount.identifier,
            "description": subaccount.description,
        }
    }
    actual.refresh_from_db()
    assert actual.payment_id == "Payment ID"


def test_change_actual_parent_to_subaccount(api_client, user, f):
    budget = f.create_budget()
    account = f.create_budget_account(parent=budget)
    markup = f.create_markup(parent=account)
    subaccount = f.create_budget_subaccount(parent=account, markups=[markup])
    actuals = [
        f.create_actual(owner=markup, budget=budget, value=100.0),
        f.create_actual(owner=markup, budget=budget, value=50.0)
    ]

    markup.refresh_from_db()
    assert markup.actual == 150.0

    account.refresh_from_db()
    assert account.actual == 150.0

    subaccount.refresh_from_db()
    assert subaccount.actual == 0.0

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
        "name": actuals[0].name,
        "notes": actuals[0].notes,
        "purchase_order": "%s" % actuals[0].purchase_order,
        "date": actuals[0].date,
        "payment_id": actuals[0].payment_id,
        "value": actuals[0].value,
        "contact": actuals[0].contact,
        "actual_type": None,
        "attachments": [],
        "order": "n",
        "owner": {
            "id": subaccount.pk,
            "type": "subaccount",
            "identifier": subaccount.identifier,
            "description": subaccount.description
        }
    }
    subaccount.refresh_from_db()
    assert subaccount.actual == 100.0

    # The account will still have an actual value of 150.0 because it still
    # has a sum of 150.0 across the actuals of it's children (actual child or
    # markup child).
    account.refresh_from_db()
    assert account.actual == 150.0

    markup.refresh_from_db()
    assert markup.actual == 50.0

    actuals[0].refresh_from_db()
    assert actuals[0].budget == budget
    assert actuals[0].owner == subaccount


def test_change_actual_parent_to_markup(api_client, user, f):
    budget = f.create_budget()
    account = f.create_budget_account(parent=budget)
    markup = f.create_markup(parent=account)
    subaccount = f.create_budget_subaccount(parent=account, markups=[markup])
    actuals = [
        f.create_actual(owner=subaccount, budget=budget, value=100.0),
        f.create_actual(owner=subaccount, budget=budget, value=50.0)
    ]

    markup.refresh_from_db()
    assert markup.actual == 0.0

    account.refresh_from_db()
    assert account.actual == 150.0

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
        "name": actuals[0].name,
        "notes": actuals[0].notes,
        "purchase_order": "%s" % actuals[0].purchase_order,
        "date": actuals[0].date,
        "payment_id": actuals[0].payment_id,
        "value": actuals[0].value,
        "contact": actuals[0].contact,
        "actual_type": None,
        "attachments": [],
        "order": "n",
        "owner": {
            "id": markup.pk,
            "type": "markup",
            "identifier": markup.identifier,
            "description": markup.description,
        }
    }
    subaccount.refresh_from_db()
    assert subaccount.actual == 50.0

    # The account will still have an actual value of 150.0 because it still
    # has a sum of 150.0 across the actuals of it's children (actual child or
    # markup child).
    account.refresh_from_db()
    assert account.actual == 150.0

    markup.refresh_from_db()
    assert markup.actual == 100.0

    actuals[0].refresh_from_db()
    assert actuals[0].budget == budget
    assert actuals[0].owner == markup


def test_change_actual_owner_invalid_subaccount(api_client, user, f):
    budgets = [f.create_budget(), f.create_budget()]
    account = f.create_budget_account(parent=budgets[0])
    subaccount = f.create_budget_subaccount(parent=account)
    another_account = f.create_budget_account(parent=budgets[1])
    another_subaccount = f.create_budget_subaccount(parent=another_account)
    actual = f.create_actual(owner=subaccount, budget=budgets[0])

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actual.pk,
        format="json",
        data={"owner": {"type": "subaccount", "id": another_subaccount.pk}}
    )
    assert response.status_code == 400


def test_change_actual_owner_invalid_markup(api_client, user, f):
    budgets = [f.create_budget(), f.create_budget()]

    account = f.create_budget_account(parent=budgets[0])
    subaccount = f.create_budget_subaccount(parent=account)

    another_account = f.create_budget_account(parent=budgets[1])
    another_subaccount = f.create_budget_subaccount(parent=another_account)
    markup = f.create_markup(parent=another_subaccount)

    actual = f.create_actual(owner=subaccount, budget=budgets[0])

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actual.pk,
        format="json",
        data={"owner": {"type": "markup", "id": markup.pk}}
    )
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_delete_actual(api_client, user, f, freezer, models):
    budget = f.create_budget(created_by=user)
    actual = f.create_actual(budget=budget, created_by=user)

    api_client.force_login(user)
    freezer.move_to("2020-01-02")
    response = api_client.delete("/v1/actuals/%s/" % actual.pk)
    assert response.status_code == 204
    assert models.Actual.objects.count() == 0

    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(2020, 1, 2).replace(
        tzinfo=datetime.timezone.utc)
    assert budget.updated_by == user


@pytest.mark.freeze_time('2020-01-01')
@override_settings(STAFF_USER_GLOBAL_PERMISSIONS=True)
def test_delete_actual_as_staff_user(api_client, user, staff_user, f, freezer,
        models):
    budget = f.create_budget(created_by=user)
    actual = f.create_actual(budget=budget, created_by=user)

    # Login as the staff user because the staff user should be able to delete
    # another user's actual.
    api_client.force_login(staff_user)

    freezer.move_to("2020-01-02")
    response = api_client.delete("/v1/actuals/%s/" % actual.pk)
    assert response.status_code == 204
    assert models.Actual.objects.count() == 0

    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(2020, 1, 2).replace(
        tzinfo=datetime.timezone.utc)
    assert budget.updated_by == staff_user
