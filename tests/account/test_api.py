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
            "identifier": "%s" % accounts[0].identifier,
            "description": accounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "access": [],
            "budget": budget.pk,
            "type": "account",
            "estimated": None,
            "variance": None,
            "actual": None,
            "subaccounts": [],
            "group": None,
            "ancestors": [{
                "type": "budget",
                "id": budget.pk,
                "identifier": budget.name
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
                "full_name": user.full_name,
                "profile_image": None,
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
                "full_name": user.full_name,
                "profile_image": None,
            }
        },
        {
            "id": accounts[1].pk,
            "identifier": "%s" % accounts[1].identifier,
            "description": accounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "access": [],
            "budget": budget.pk,
            "type": "account",
            "estimated": None,
            "variance": None,
            "actual": None,
            "subaccounts": [],
            "group": None,
            "ancestors": [{
                "type": "budget",
                "id": budget.pk,
                "identifier": budget.name
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
                "full_name": user.full_name,
                "profile_image": None,
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
                "full_name": user.full_name,
                "profile_image": None,
            }
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_account(api_client, user, create_account, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": account.pk,
        "identifier": "%s" % account.identifier,
        "description": account.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "budget": account.budget.pk,
        "type": "account",
        "estimated": None,
        "variance": None,
        "actual": None,
        "subaccounts": [],
        "group": None,
        "ancestors": [{
            "type": "budget",
            "id": account.budget.pk,
            "identifier": account.budget.name
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
            "full_name": user.full_name,
            "profile_image": None,
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
            "full_name": user.full_name,
            "profile_image": None,
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_account(api_client, user, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.post("/v1/budgets/%s/accounts/" % budget.pk, data={
        'identifier': 'new_account'
    })
    assert response.status_code == 201

    account = Account.objects.first()
    assert account is not None

    assert response.json() == {
        "id": account.pk,
        "identifier": 'new_account',
        "description": None,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "budget": budget.pk,
        "type": "account",
        "estimated": None,
        "variance": None,
        "actual": None,
        "subaccounts": [],
        "group": None,
        "ancestors": [{
            "type": "budget",
            "id": budget.pk,
            "identifier": budget.name
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
            "full_name": user.full_name,
            "profile_image": None,
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
            "full_name": user.full_name,
            "profile_image": None,
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_account_duplicate_number(api_client, user, create_budget,
        create_account):
    api_client.force_login(user)
    budget = create_budget()
    create_account(budget=budget, identifier="new_account")
    response = api_client.post("/v1/budgets/%s/accounts/" % budget.pk, data={
        'identifier': 'new_account'
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_update_account(api_client, user, create_budget, create_account):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(
        budget=budget,
        identifier="original_identifier"
    )
    response = api_client.patch("/v1/accounts/%s/" % account.pk, data={
        'identifier': 'new_account',
        'description': 'Account description',
    })
    assert response.status_code == 200
    assert response.json() == {
        "id": account.pk,
        "identifier": 'new_account',
        "description": 'Account description',
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "budget": budget.pk,
        "type": "account",
        "estimated": None,
        "variance": None,
        "actual": None,
        "subaccounts": [],
        "group": None,
        "ancestors": [{
            "type": "budget",
            "id": budget.pk,
            "identifier": budget.name
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
            "full_name": user.full_name,
            "profile_image": None,
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
            "full_name": user.full_name,
            "profile_image": None,
        }
    }
    account.refresh_from_db()
    assert account.identifier == "new_account"
    assert account.description == "Account description"


@pytest.mark.freeze_time('2020-01-01')
def test_update_account_duplicate_number(api_client, user, create_budget,
        create_account):
    api_client.force_login(user)
    budget = create_budget()
    create_account(identifier="identifier", budget=budget)
    account = create_account(
        budget=budget,
        identifier="original_identifier"
    )
    response = api_client.patch("/v1/accounts/%s/" % account.pk, data={
        'identifier': 'identifier',
        'description': 'Account description',
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_account(api_client, user, create_budget, create_account,
        create_sub_account):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    subaccounts = [
        create_sub_account(budget=budget, parent=account),
        create_sub_account(budget=budget, parent=account)
    ]
    response = api_client.patch(
        "/v1/accounts/%s/bulk-update/" % account.pk,
        format='json',
        data={
            'changes': [
                {
                    'id': subaccounts[0].pk,
                    'name': 'New Name 1',
                },
                {
                    'id': subaccounts[1].pk,
                    'name': 'New Name 2',
                }
            ]
        })
    assert response.json()['subaccounts'][0]['name'] == 'New Name 1'
    assert response.json()['subaccounts'][1]['name'] == 'New Name 2'
