import pytest

from greenbudget.app.actual.models import Actual


@pytest.mark.freeze_time('2020-01-01')
def test_create_actual(api_client, user, create_account,
        create_budget):
    budget = create_budget()
    account = create_account(budget=budget)
    api_client.force_login(user)
    response = api_client.post(
        "/v1/accounts/%s/actuals/" % account.pk,
        data={"object_id": account.pk, "parent_type": "account"}
    )
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
        "payment_method_name": "",
        "object_id": account.pk,
        "parent_type": "account",
        "vendor": None,
        "created_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name
        },
        "updated_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name
        }
    }
    actual = Actual.objects.first()
    assert actual is not None
    assert actual.budget == budget
    assert actual.parent == account


def test_create_actual_invalid_parent(api_client, user, create_account,
        create_budget):
    budgets = [create_budget(), create_budget()]
    accounts = [
        create_account(budget=budgets[0]),
        create_account(budget=budgets[1])
    ]
    api_client.force_login(user)
    response = api_client.post(
        "/v1/accounts/%s/actuals/" % accounts[0].pk,
        data={"object_id": accounts[1].pk, "parent_type": "account"}
    )
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_update_actual(api_client, user, create_account,
        create_budget, create_actual):
    budget = create_budget()
    account = create_account(budget=budget)
    another_account = create_account(budget=budget)
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
        "value": "{:.2f}".format(actual.value),
        "payment_method": actual.payment_method,
        "payment_method_name": actual.PAYMENT_METHODS[actual.payment_method],
        "object_id": another_account.pk,
        "parent_type": "account",
        "vendor": actual.vendor,
        "created_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name
        },
        "updated_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name
        }
    }
    actual.refresh_from_db()
    assert actual.budget == budget
    assert actual.parent == another_account


@pytest.mark.freeze_time('2020-01-01')
def test_get_account_actuals(api_client, user, create_account, create_actual,
        create_budget):
    budget = create_budget()
    account = create_account(budget=budget)
    actuals = [
        create_actual(parent=account, budget=budget),
        create_actual(parent=account, budget=budget)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/actuals/" % account.pk)
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
            "value": "{:.2f}".format(actuals[0].value),
            "payment_method": actuals[0].payment_method,
            "payment_method_name": Actual.PAYMENT_METHODS[
                actuals[0].payment_method],
            "object_id": account.pk,
            "parent_type": "account",
            "created_by": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name
            },
            "updated_by": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name
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
            "value": "{:.2f}".format(actuals[1].value),
            "payment_method": actuals[1].payment_method,
            "payment_method_name": Actual.PAYMENT_METHODS[
                actuals[1].payment_method],
            "object_id": account.pk,
            "parent_type": "account",
            "created_by": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name
            },
            "updated_by": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name
            }
        },
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount_actuals(api_client, user, create_sub_account,
        create_actual, create_budget):
    budget = create_budget()
    sub_account = create_sub_account(budget=budget)
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
            "value": "{:.2f}".format(actuals[0].value),
            "payment_method": actuals[0].payment_method,
            "payment_method_name": Actual.PAYMENT_METHODS[
                actuals[0].payment_method],
            "object_id": sub_account.pk,
            "parent_type": "subaccount",
            "created_by": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name
            },
            "updated_by": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name
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
            "value": "{:.2f}".format(actuals[1].value),
            "payment_method": actuals[1].payment_method,
            "payment_method_name": Actual.PAYMENT_METHODS[
                actuals[1].payment_method],
            "object_id": sub_account.pk,
            "parent_type": "subaccount",
            "created_by": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name
            },
            "updated_by": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name
            }
        },
    ]
