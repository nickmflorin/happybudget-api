import pytest

from greenbudget.app.account.models import Account


@pytest.mark.freeze_time('2020-01-01')
def test_get_accounts(api_client, user, create_account, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    accounts = [create_account(budget=budget), create_account(budget=budget)]
    response = api_client.get("/v1/budgets/%s/accounts/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": accounts[0].pk,
            "account_number": "%s" % accounts[0].account_number,
            "description": accounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "access": [],
            "budget": budget.pk,
            "estimated": None,
            "subaccounts": [],
            "ancestors": [{
                "type": "budget",
                "id": budget.pk,
                "name": budget.name
            }],
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
            "id": accounts[1].pk,
            "account_number": "%s" % accounts[1].account_number,
            "description": accounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "access": [],
            "budget": budget.pk,
            "estimated": None,
            "subaccounts": [],
            "ancestors": [{
                "type": "budget",
                "id": budget.pk,
                "name": budget.name
            }],
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
def test_get_account(api_client, user, create_account):
    api_client.force_login(user)
    account = create_account()
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": account.pk,
        "account_number": "%s" % account.account_number,
        "description": account.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "budget": account.budget.pk,
        "estimated": None,
        "subaccounts": [],
        "ancestors": [{
            "type": "budget",
            "id": account.budget.pk,
            "name": account.budget.name
        }],
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
def test_create_account(api_client, user, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.post("/v1/budgets/%s/accounts/" % budget.pk, data={
        'account_number': 'new_account'
    })
    assert response.status_code == 201

    account = Account.objects.first()
    assert account is not None

    assert response.json() == {
        "id": account.pk,
        "account_number": 'new_account',
        "description": None,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "budget": budget.pk,
        "estimated": None,
        "subaccounts": [],
        "ancestors": [{
            "type": "budget",
            "id": budget.pk,
            "name": budget.name
        }],
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
def test_create_account_duplicate_number(api_client, user, create_budget,
        create_account):
    api_client.force_login(user)
    budget = create_budget()
    create_account(budget=budget, account_number="new_account")
    response = api_client.post("/v1/budgets/%s/accounts/" % budget.pk, data={
        'account_number': 'new_account'
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_update_account(api_client, user, create_budget, create_account):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(
        budget=budget,
        account_number="original_account_number"
    )
    response = api_client.patch("/v1/accounts/%s/" % account.pk, data={
        'account_number': 'new_account',
        'description': 'Account description',
    })
    assert response.status_code == 200
    assert response.json() == {
        "id": account.pk,
        "account_number": 'new_account',
        "description": 'Account description',
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "budget": budget.pk,
        "estimated": None,
        "subaccounts": [],
        "ancestors": [{
            "type": "budget",
            "id": budget.pk,
            "name": budget.name
        }],
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
    account.refresh_from_db()
    assert account.account_number == "new_account"
    assert account.description == "Account description"


@pytest.mark.freeze_time('2020-01-01')
def test_update_account_duplicate_number(api_client, user, create_budget,
        create_account):
    api_client.force_login(user)
    budget = create_budget()
    create_account(account_number="account_number", budget=budget)
    account = create_account(
        budget=budget,
        account_number="original_account_number"
    )
    response = api_client.patch("/v1/accounts/%s/" % account.pk, data={
        'account_number': 'account_number',
        'description': 'Account description',
    })
    assert response.status_code == 400
