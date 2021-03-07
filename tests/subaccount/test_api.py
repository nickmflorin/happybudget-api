import pytest

from greenbudget.app.subaccount.models import SubAccount


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount(api_client, user, create_sub_account, create_account,
        create_budget):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(content_object=account)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": subaccount.pk,
        "name": subaccount.name,
        "line": "%s" % subaccount.line,
        "description": subaccount.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": subaccount.quantity,
        "rate": "{:.2f}".format(subaccount.rate),
        "multiplier": "{:.2f}".format(subaccount.multiplier),
        "unit": subaccount.unit,
        "unit_name": subaccount.unit_name,
        "parent": account.pk,
        "parent_type": "account",
        "account": account.pk,
        "estimated": None,
        "subaccounts": [],
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


@pytest.mark.freeze_time('2020-01-01')
def test_create_subaccount(api_client, user, create_account, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    response = api_client.post(
        "/v1/budgets/%s/accounts/%s/subaccounts/" % (budget.pk, account.pk),
        data={'name': 'New Subaccount', 'line': '100', 'description': 'Test'}
    )
    assert response.status_code == 201
    subaccount = SubAccount.objects.first()
    assert subaccount.name == "New Subaccount"
    assert subaccount.description == "Test"
    assert subaccount.line == "100"

    assert subaccount is not None
    assert response.json() == {
        "id": subaccount.pk,
        "name": 'New Subaccount',
        "line": '100',
        "description": 'Test',
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": None,
        "rate": None,
        "multiplier": None,
        "unit": None,
        "unit_name": '',
        "parent": account.pk,
        "parent_type": "account",
        "account": account.pk,
        "estimated": None,
        "subaccounts": [],
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


@pytest.mark.freeze_time('2020-01-01')
def test_update_subaccount(api_client, user, create_sub_account, create_account,
        create_budget):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(
        content_object=account,
        name="Original Name",
        description="Original Description",
        line="Original Line"
    )
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "name": "New Name",
        "description": "New Description",
        "line": "New Line",
        "quantity": 10,
        "rate": 1.5
    })
    assert response.status_code == 200
    subaccount.refresh_from_db()
    assert response.json() == {
        "id": subaccount.pk,
        "name": "New Name",
        "line": "New Line",
        "description": "New Description",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": 10,
        "rate": "1.50",
        "multiplier": "{:.2f}".format(subaccount.multiplier),
        "unit": subaccount.unit,
        "unit_name": subaccount.unit_name,
        "parent": account.pk,
        "parent_type": "account",
        "account": account.pk,
        "estimated": '15.00',
        "subaccounts": [],
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

    assert subaccount.name == "New Name"
    assert subaccount.description == "New Description"
    assert subaccount.line == "New Line"
    assert subaccount.quantity == 10
    assert subaccount.rate == 1.5


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
            "estimated": None,
            "subaccounts": [],
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
            "estimated": None,
            "subaccounts": [],
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
def test_get_subaccount_subaccounts(api_client, user, create_sub_account,
        create_budget, create_account):

    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    parent = create_sub_account(content_object=account)
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
            "estimated": None,
            "subaccounts": [],
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
                },
                {
                    "id": parent.id,
                    "type": "subaccount",
                    "name": parent.name,
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
            "parent": parent.pk,
            "parent_type": "subaccount",
            "account": parent.account.pk,
            "estimated": None,
            "subaccounts": [],
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
                },
                {
                    "id": parent.id,
                    "type": "subaccount",
                    "name": parent.name,
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
