import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_account_subaccounts(api_client, user, create_account,
        create_budget, create_sub_account):

    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    another_account = create_account(budget=budget)
    subaccounts = [
        create_sub_account(content_object=account),
        create_sub_account(content_object=account),
        create_sub_account(content_object=another_account)
    ]
    response = api_client.get(
        "/v1/budgets/%s/accounts/%s/subaccounts/"
        % (budget.pk, account.pk)
    )
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": subaccounts[0].pk,
            "name": subaccounts[0].name,
            "line": "%s" % subaccounts[0].line,
            "description": subaccounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[0].quantity,
            "rate": "{:.2f}".format(subaccounts[0].rate),
            "multiplier": "{:.2f}".format(subaccounts[0].multiplier),
            "unit": subaccounts[0].unit,
            "unit_name": subaccounts[0].unit_name,
            "parent": account.pk,
            "parent_type": "account",
            "account": account.pk,
            "ancestors": [
                {
                    "id": budget.id,
                    "type": "budget",
                    "name": budget.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "name": '%s' % account.account_number,
                }
            ],
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
            "id": subaccounts[1].pk,
            "name": subaccounts[1].name,
            "line": "%s" % subaccounts[1].line,
            "description": subaccounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[1].quantity,
            "rate": "{:.2f}".format(subaccounts[1].rate),
            "multiplier": "{:.2f}".format(subaccounts[1].multiplier),
            "unit": subaccounts[1].unit,
            "unit_name": subaccounts[1].unit_name,
            "parent": account.pk,
            "parent_type": "account",
            "account": account.pk,
            "ancestors": [
                {
                    "id": budget.id,
                    "type": "budget",
                    "name": budget.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "name": '%s' % account.account_number,
                }
            ],
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
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount_subaccounts(api_client, user, create_sub_account):

    api_client.force_login(user)
    parent = create_sub_account()
    another_parent = create_sub_account()
    subaccounts = [
        create_sub_account(content_object=parent),
        create_sub_account(content_object=parent),
        create_sub_account(content_object=another_parent)
    ]
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % parent.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": subaccounts[0].pk,
            "name": subaccounts[0].name,
            "line": "%s" % subaccounts[0].line,
            "description": subaccounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[0].quantity,
            "rate": "{:.2f}".format(subaccounts[0].rate),
            "multiplier": "{:.2f}".format(subaccounts[0].multiplier),
            "unit": subaccounts[0].unit,
            "unit_name": subaccounts[0].unit_name,
            "parent": parent.pk,
            "parent_type": "subaccount",
            "account": parent.account.pk,
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
            "id": subaccounts[1].pk,
            "name": subaccounts[1].name,
            "line": "%s" % subaccounts[1].line,
            "description": subaccounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[1].quantity,
            "rate": "{:.2f}".format(subaccounts[1].rate),
            "multiplier": "{:.2f}".format(subaccounts[1].multiplier),
            "unit": subaccounts[1].unit,
            "unit_name": subaccounts[1].unit_name,
            "parent": parent.pk,
            "parent_type": "subaccount",
            "account": parent.account.pk,
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
    ]
