import pytest

from greenbudget.app.actual.models import Actual


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
            "parent": account.pk,
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
            "parent": account.pk,
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
            "parent": sub_account.pk,
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
            "parent": sub_account.pk,
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
