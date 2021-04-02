import pytest

from greenbudget.lib.utils.dateutils import api_datetime_string

from greenbudget.app.account.models import Account
from greenbudget.app.budget.models import Budget


@pytest.mark.freeze_time('2020-01-01')
def test_get_budgets(api_client, user, create_budget):
    api_client.force_login(user)
    budgets = [create_budget(), create_budget()]
    response = api_client.get("/v1/budgets/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": budgets[0].pk,
            "name": budgets[0].name,
            "project_number": budgets[0].project_number,
            "production_type": budgets[0].production_type,
            "production_type_name": budgets[0].production_type_name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "shoot_date": api_datetime_string(budgets[0].shoot_date),
            "delivery_date": api_datetime_string(budgets[0].delivery_date),
            "build_days": budgets[0].build_days,
            "prelight_days": budgets[0].prelight_days,
            "studio_shoot_days": budgets[0].studio_shoot_days,
            "location_days": budgets[0].location_days,
            "estimated": None,
            "variance": None,
            "actual": None,
            'trash': False,
            "author": {
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
        },
        {
            "id": budgets[1].pk,
            "name": budgets[1].name,
            "project_number": budgets[1].project_number,
            "production_type": budgets[1].production_type,
            "production_type_name": budgets[1].production_type_name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "shoot_date": api_datetime_string(budgets[1].shoot_date),
            "delivery_date": api_datetime_string(budgets[1].delivery_date),
            "build_days": budgets[1].build_days,
            "prelight_days": budgets[1].prelight_days,
            "studio_shoot_days": budgets[1].studio_shoot_days,
            "location_days": budgets[1].location_days,
            "estimated": None,
            "variance": None,
            "actual": None,
            'trash': False,
            "author": {
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
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget(api_client, user, create_budget, db):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "project_number": budget.project_number,
        "production_type": budget.production_type,
        "production_type_name": budget.production_type_name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "shoot_date": api_datetime_string(budget.shoot_date),
        "delivery_date": api_datetime_string(budget.delivery_date),
        "build_days": budget.build_days,
        "prelight_days": budget.prelight_days,
        "studio_shoot_days": budget.studio_shoot_days,
        "location_days": budget.location_days,
        "trash": False,
        "estimated": None,
        "variance": None,
        "actual": None,
        "author": {
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
def test_create_budget(api_client, user, db):
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/", data={
        "name": "Test Name",
        "production_type": 1,
    })
    assert response.status_code == 201

    budget = Budget.objects.first()
    assert budget is not None

    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "project_number": budget.project_number,
        "production_type": 1,
        "production_type_name": budget.PRODUCTION_TYPES[1],
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "shoot_date": api_datetime_string(budget.shoot_date),
        "delivery_date": api_datetime_string(budget.delivery_date),
        "build_days": budget.build_days,
        "prelight_days": budget.prelight_days,
        "studio_shoot_days": budget.studio_shoot_days,
        "location_days": budget.location_days,
        'trash': False,
        "estimated": None,
        "variance": None,
        "actual": None,
        "author": {
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
def test_create_budget_non_unique_name(api_client, user, create_budget, db):
    existing = create_budget()
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/", data={
        "name": existing.name,
        "production_type": 1,
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_get_budgets_in_trash(api_client, user, create_budget, db):
    api_client.force_login(user)
    budgets = [
        create_budget(trash=True),
        create_budget(trash=True),
        create_budget()
    ]
    response = api_client.get("/v1/budgets/trash/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": budgets[0].pk,
            "name": budgets[0].name,
            "project_number": budgets[0].project_number,
            "production_type": budgets[0].production_type,
            "production_type_name": budgets[0].production_type_name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "shoot_date": api_datetime_string(budgets[0].shoot_date),
            "delivery_date": api_datetime_string(budgets[0].delivery_date),
            "build_days": budgets[0].build_days,
            "prelight_days": budgets[0].prelight_days,
            "studio_shoot_days": budgets[0].studio_shoot_days,
            "location_days": budgets[0].location_days,
            'trash': True,
            "estimated": None,
            "variance": None,
            "actual": None,
            "author": {
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
        },
        {
            "id": budgets[1].pk,
            "name": budgets[1].name,
            "project_number": budgets[1].project_number,
            "production_type": budgets[1].production_type,
            "production_type_name": budgets[1].production_type_name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "shoot_date": api_datetime_string(budgets[1].shoot_date),
            "delivery_date": api_datetime_string(budgets[1].delivery_date),
            "build_days": budgets[1].build_days,
            "prelight_days": budgets[1].prelight_days,
            "studio_shoot_days": budgets[1].studio_shoot_days,
            "location_days": budgets[1].location_days,
            'trash': True,
            "estimated": None,
            "variance": None,
            "actual": None,
            "author": {
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
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_in_trash(api_client, user, create_budget, db):
    api_client.force_login(user)
    budget = create_budget(trash=True)
    response = api_client.get("/v1/budgets/trash/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "project_number": budget.project_number,
        "production_type": budget.production_type,
        "production_type_name": budget.production_type_name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "shoot_date": api_datetime_string(budget.shoot_date),
        "delivery_date": api_datetime_string(budget.delivery_date),
        "build_days": budget.build_days,
        "prelight_days": budget.prelight_days,
        "studio_shoot_days": budget.studio_shoot_days,
        "location_days": budget.location_days,
        'trash': True,
        "estimated": None,
        "variance": None,
        "actual": None,
        "author": {
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
def test_delete_budget(api_client, user, create_budget, db):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.delete("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 204

    budget.refresh_from_db()
    assert budget.trash is True
    assert budget.id is not None


@pytest.mark.freeze_time('2020-01-01')
def test_restore_budget(api_client, user, create_budget, db):
    api_client.force_login(user)
    budget = create_budget(trash=True)
    response = api_client.patch("/v1/budgets/trash/%s/restore/" % budget.pk)
    assert response.status_code == 201

    assert response.json()['id'] == budget.pk
    assert response.json()['trash'] is False

    budget.refresh_from_db()
    assert budget.trash is False


@pytest.mark.freeze_time('2020-01-01')
def test_permanently_delete_budget(api_client, user, create_budget, db):
    api_client.force_login(user)
    budget = create_budget(trash=True)
    response = api_client.delete("/v1/budgets/trash/%s/" % budget.pk)
    assert response.status_code == 204

    assert Budget.objects.first() is None


def test_get_budget_items(api_client, user, create_budget, create_account,
        create_sub_account):
    budget = create_budget()
    account = create_account(budget=budget, identifier="Account A")
    create_sub_account(budget=budget, identifier="Jack")
    api_client.force_login(user)
    response = api_client.get(
        "/v1/budgets/%s/items/?search=%s"
        % (budget.pk, "Account")
    )
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
        'id': account.pk,
        'identifier': 'Account A',
        'description': account.description,
        'type': 'account'
    }]


def test_get_budget_items_tree(api_client, user, create_budget, create_account,
        create_sub_account):
    budget = create_budget()
    accounts = [
        create_account(budget=budget, identifier="Account A"),
        create_account(budget=budget, identifier="Account B"),
    ]
    subaccounts = [
        [
            create_sub_account(
                budget=budget,
                parent=accounts[0],
                identifier="Sub Account A-A"
            ),
            create_sub_account(
                budget=budget,
                parent=accounts[0],
                identifier="Sub Account A-B"
            ),
            create_sub_account(
                budget=budget,
                parent=accounts[0],
                identifier="Sub Account A-C"
            )
        ],
        [
            create_sub_account(
                budget=budget,
                parent=accounts[1],
                identifier="Sub Account B-A"
            ),
            create_sub_account(
                budget=budget,
                parent=accounts[1],
                identifier="Sub Account B-B"
            ),
            create_sub_account(
                budget=budget,
                parent=accounts[1],
                identifier="Sub Account B-C"
            )
        ]
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/items/tree/" % budget.pk)

    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": accounts[0].pk,
            "identifier": "Account A",
            "type": "account",
            "description": accounts[0].description,
            "children": [
                {
                    "id": subaccounts[0][0].pk,
                    "identifier": "Sub Account A-A",
                    "type": "subaccount",
                    "description": subaccounts[0][0].description,
                    "children": []
                },
                {
                    "id": subaccounts[0][1].pk,
                    "identifier": "Sub Account A-B",
                    "type": "subaccount",
                    "description": subaccounts[0][1].description,
                    "children": []
                },
                {
                    "id": subaccounts[0][2].pk,
                    "identifier": "Sub Account A-C",
                    "type": "subaccount",
                    "description": subaccounts[0][2].description,
                    "children": []
                }
            ]
        },
        {
            "id": accounts[1].pk,
            "identifier": "Account B",
            "type": "account",
            "description": accounts[1].description,
            "children": [
                {
                    "id": subaccounts[1][0].pk,
                    "identifier": "Sub Account B-A",
                    "type": "subaccount",
                    "description": subaccounts[1][0].description,
                    "children": []
                },
                {
                    "id": subaccounts[1][1].pk,
                    "identifier": "Sub Account B-B",
                    "type": "subaccount",
                    "description": subaccounts[1][1].description,
                    "children": []
                },
                {
                    "id": subaccounts[1][2].pk,
                    "identifier": "Sub Account B-C",
                    "type": "subaccount",
                    "description": subaccounts[1][2].description,
                    "children": []
                }
            ]
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_accounts(api_client, user, create_budget,
        create_account):
    api_client.force_login(user)
    budget = create_budget()
    accounts = [
        create_account(budget=budget),
        create_account(budget=budget)
    ]
    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-accounts/" % budget.pk,
        format='json',
        data={
            'data': [
                {
                    'id': accounts[0].pk,
                    'description': 'New Description 1',
                },
                {
                    'id': accounts[1].pk,
                    'description': 'New Description 2',
                }
            ]
        })
    assert response.status_code == 200

    accounts[0].refresh_from_db()
    assert accounts[0].description == "New Description 1"
    accounts[1].refresh_from_db()
    assert accounts[1].description == "New Description 2"


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_accounts_outside_budget(api_client, user,
        create_budget, create_account):
    api_client.force_login(user)
    budget = create_budget()
    another_budget = create_budget()
    accounts = [
        create_account(budget=budget),
        create_account(budget=another_budget)
    ]
    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-accounts/" % budget.pk,
        format='json',
        data={
            'data': [
                {
                    'id': accounts[0].pk,
                    'description': 'New Description 1',
                },
                {
                    'id': accounts[1].pk,
                    'description': 'New Description 2',
                }
            ]
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_budget_accounts(api_client, user, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.patch(
        "/v1/budgets/%s/bulk-create-accounts/" % budget.pk,
        format='json',
        data={
            'data': [
                {
                    'identifier': 'account-a',
                    'description': 'New Description 1',
                },
                {
                    'identifier': 'account-b',
                    'description': 'New Description 2',
                }
            ]
        })
    assert response.status_code == 201

    accounts = Account.objects.all()
    assert len(accounts) == 2
    assert accounts[0].identifier == "account-a"
    assert accounts[0].description == "New Description 1"
    assert accounts[0].budget == budget
    assert accounts[1].description == "New Description 2"
    assert accounts[1].identifier == "account-b"
    assert accounts[1].budget == budget

    assert response.json()['data'][0]['identifier'] == 'account-a'
    assert response.json()['data'][0]['description'] == 'New Description 1'
    assert response.json()['data'][1]['identifier'] == 'account-b'
    assert response.json()['data'][1]['description'] == 'New Description 2'


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_actuals(api_client, user, create_budget,
        create_account, create_actual):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    actuals = [
        create_actual(parent=account, budget=budget),
        create_actual(parent=account, budget=budget)
    ]
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
