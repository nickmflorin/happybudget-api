import pytest

from greenbudget.lib.utils.dateutils import api_datetime_string

from greenbudget.app.account.models import Account
from greenbudget.app.budget.models import Budget
from greenbudget.app.fringe.models import Fringe


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
            "production_type": {
                "id": budgets[0].production_type,
                "name": Budget.PRODUCTION_TYPES[budgets[0].production_type]
            },
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
            "created_by": user.pk,
            "type": "budget"
        },
        {
            "id": budgets[1].pk,
            "name": budgets[1].name,
            "project_number": budgets[1].project_number,
            "production_type": {
                "id": budgets[1].production_type,
                "name": Budget.PRODUCTION_TYPES[budgets[1].production_type]
            },
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
            "created_by": user.pk,
            "type": "budget"
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget(api_client, user, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "project_number": budget.project_number,
        "production_type": {
            "id": budget.production_type,
            "name": Budget.PRODUCTION_TYPES[budget.production_type]
        },
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
        "created_by": user.pk,
        "type": "budget"
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget(api_client, user, create_budget):
    budget = create_budget()
    api_client.force_login(user)
    response = api_client.patch("/v1/budgets/%s/" % budget.pk, data={
         "name": "New Name"
    })
    assert response.status_code == 200
    budget.refresh_from_db()
    assert budget.name == "New Name"
    assert response.json() == {
        "id": budget.pk,
        "name": "New Name",
        "project_number": budget.project_number,
        "production_type": {
            "id": budget.production_type,
            "name": Budget.PRODUCTION_TYPES[budget.production_type]
        },
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
        "created_by": user.pk,
        "type": "budget"
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget(api_client, user):
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
        "production_type": {
            "id": 1,
            "name": Budget.PRODUCTION_TYPES[1],
        },
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
        "created_by": user.pk,
        "type": "budget"
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_from_template(api_client, user, create_template,
        create_template_account, create_template_subaccount, admin_user,
        create_fringe, create_template_account_group,
        create_template_subaccount_group):
    template = create_template(created_by=admin_user)
    fringes = [
        create_fringe(
            budget=template,
            created_by=admin_user,
            updated_by=admin_user
        ),
        create_fringe(
            budget=template,
            created_by=admin_user,
            updated_by=admin_user
        ),
    ]
    template_account_group = create_template_account_group(parent=template)
    accounts = [
        create_template_account(
            budget=template,
            created_by=admin_user,
            updated_by=admin_user,
            group=template_account_group,
        ),
        create_template_account(
            budget=template,
            created_by=admin_user,
            updated_by=admin_user,
            group=template_account_group,
        )
    ]
    template_subaccount_group = create_template_subaccount_group(
        parent=accounts[0])
    subaccounts = [
        create_template_subaccount(
            parent=accounts[0],
            budget=template,
            created_by=admin_user,
            updated_by=admin_user,
            group=template_subaccount_group
        ),
        create_template_subaccount(
            parent=accounts[1],
            budget=template,
            created_by=admin_user,
            updated_by=admin_user
        )
    ]
    child_subaccounts = [
        create_template_subaccount(
            parent=subaccounts[0],
            budget=template,
            created_by=admin_user,
            updated_by=admin_user
        ),
        create_template_subaccount(
            parent=subaccounts[1],
            budget=template,
            created_by=admin_user,
            updated_by=admin_user
        )
    ]
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/", data={
        "name": "Test Name",
        "production_type": 1,
        "template": template.pk,
    })
    assert response.status_code == 201
    assert response.json()['name'] == 'Test Name'
    assert response.json()['production_type'] == {
        "id": 1,
        "name": Budget.PRODUCTION_TYPES[1],
    }

    budget = Budget.objects.first()
    assert budget is not None
    assert budget.name == "Test Name"
    assert budget.accounts.count() == 2
    assert budget.created_by == user

    assert budget.groups.count() == 1
    budget_account_group = budget.groups.first()
    assert budget_account_group.name == template_account_group.name
    assert budget_account_group.color == template_account_group.color

    assert budget.fringes.count() == 2

    first_fringe = budget.fringes.first()
    assert first_fringe.created_by == user
    assert first_fringe.updated_by == user
    assert first_fringe.name == fringes[0].name
    assert first_fringe.description == fringes[0].description
    assert first_fringe.cutoff == fringes[0].cutoff
    assert first_fringe.rate == fringes[0].rate
    assert first_fringe.unit == fringes[0].unit

    second_fringe = budget.fringes.all()[1]
    assert second_fringe.created_by == user
    assert second_fringe.updated_by == user
    assert second_fringe.name == fringes[1].name
    assert second_fringe.description == fringes[1].description
    assert second_fringe.cutoff == fringes[1].cutoff
    assert second_fringe.rate == fringes[1].rate
    assert second_fringe.unit == fringes[1].unit

    assert budget.accounts.count() == 2

    first_account = budget.accounts.first()
    assert first_account.group == budget_account_group
    assert first_account.identifier == accounts[0].identifier
    assert first_account.description == accounts[0].description
    assert first_account.created_by == user
    assert first_account.updated_by == user

    assert first_account.subaccounts.count() == 1

    assert first_account.groups.count() == 1
    budget_subaccount_group = first_account.groups.first()
    assert budget_subaccount_group.name == template_subaccount_group.name
    assert budget_subaccount_group.color == template_subaccount_group.color

    first_account_subaccount = first_account.subaccounts.first()
    assert first_account_subaccount.group == budget_subaccount_group

    assert first_account_subaccount.created_by == user
    assert first_account_subaccount.updated_by == user
    assert first_account_subaccount.identifier == subaccounts[0].identifier
    assert first_account_subaccount.description == subaccounts[0].description
    assert first_account_subaccount.name == subaccounts[0].name
    assert first_account_subaccount.rate == subaccounts[0].rate
    assert first_account_subaccount.quantity == subaccounts[0].quantity
    assert first_account_subaccount.multiplier == subaccounts[0].multiplier
    assert first_account_subaccount.unit == subaccounts[0].unit
    assert first_account_subaccount.budget == budget

    assert first_account_subaccount.subaccounts.count() == 1
    first_account_subaccount_subaccount = first_account_subaccount.subaccounts.first()  # noqa
    assert first_account_subaccount_subaccount.created_by == user
    assert first_account_subaccount_subaccount.updated_by == user
    assert first_account_subaccount_subaccount.identifier == child_subaccounts[0].identifier  # noqa
    assert first_account_subaccount_subaccount.description == child_subaccounts[0].description  # noqa
    assert first_account_subaccount_subaccount.name == child_subaccounts[0].name  # noqa
    assert first_account_subaccount_subaccount.rate == child_subaccounts[0].rate  # noqa
    assert first_account_subaccount_subaccount.quantity == child_subaccounts[0].quantity  # noqa
    assert first_account_subaccount_subaccount.multiplier == child_subaccounts[0].multiplier  # noqa
    assert first_account_subaccount_subaccount.unit == child_subaccounts[0].unit  # noqa
    assert first_account_subaccount_subaccount.budget == budget

    second_account = budget.accounts.all()[1]
    assert second_account.group == budget_account_group
    assert second_account.identifier == accounts[1].identifier
    assert second_account.description == accounts[1].description
    assert second_account.created_by == user
    assert second_account.updated_by == user

    assert second_account.subaccounts.count() == 1
    second_account_subaccount = second_account.subaccounts.first()
    assert second_account_subaccount.created_by == user
    assert second_account_subaccount.updated_by == user
    assert second_account_subaccount.identifier == subaccounts[1].identifier
    assert second_account_subaccount.description == subaccounts[1].description
    assert second_account_subaccount.name == subaccounts[1].name
    assert second_account_subaccount.rate == subaccounts[1].rate
    assert second_account_subaccount.quantity == subaccounts[1].quantity
    assert second_account_subaccount.multiplier == subaccounts[1].multiplier
    assert second_account_subaccount.unit == subaccounts[1].unit
    assert second_account_subaccount.budget == budget

    assert second_account_subaccount.subaccounts.count() == 1
    second_account_subaccount_subaccount = second_account_subaccount.subaccounts.first()  # noqa
    assert second_account_subaccount_subaccount.created_by == user
    assert second_account_subaccount_subaccount.updated_by == user
    assert second_account_subaccount_subaccount.identifier == child_subaccounts[1].identifier  # noqa
    assert second_account_subaccount_subaccount.description == child_subaccounts[1].description  # noqa
    assert second_account_subaccount_subaccount.name == child_subaccounts[1].name  # noqa
    assert second_account_subaccount_subaccount.rate == child_subaccounts[1].rate  # noqa
    assert second_account_subaccount_subaccount.quantity == child_subaccounts[1].quantity  # noqa
    assert second_account_subaccount_subaccount.multiplier == child_subaccounts[1].multiplier  # noqa
    assert second_account_subaccount_subaccount.unit == child_subaccounts[1].unit  # noqa
    assert second_account_subaccount_subaccount.budget == budget


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
            "production_type": {
                "id": budgets[0].production_type,
                "name": Budget.PRODUCTION_TYPES[budgets[0].production_type]
            },
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
            "created_by": user.pk,
            "type": "budget"
        },
        {
            "id": budgets[1].pk,
            "name": budgets[1].name,
            "project_number": budgets[1].project_number,
            "production_type": {
                "id": budgets[1].production_type,
                "name": Budget.PRODUCTION_TYPES[budgets[1].production_type]
            },
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
            "created_by": user.pk,
            "type": "budget"
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_in_trash(api_client, user, create_budget):
    api_client.force_login(user)
    budget = create_budget(trash=True)
    response = api_client.get("/v1/budgets/trash/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "project_number": budget.project_number,
        "production_type": {
                "id": budget.production_type,
                "name": Budget.PRODUCTION_TYPES[budget.production_type]
        },
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
        "created_by": user.pk,
        "type": "budget"
    }


def test_delete_budget(api_client, user, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.delete("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 204

    budget.refresh_from_db()
    assert budget.trash is True
    assert budget.id is not None


def test_restore_budget(api_client, user, create_budget):
    api_client.force_login(user)
    budget = create_budget(trash=True)
    response = api_client.patch("/v1/budgets/trash/%s/restore/" % budget.pk)
    assert response.status_code == 201

    assert response.json()['id'] == budget.pk
    assert response.json()['trash'] is False

    budget.refresh_from_db()
    assert budget.trash is False


def test_permanently_delete_budget(api_client, user, create_budget):
    api_client.force_login(user)
    budget = create_budget(trash=True)
    response = api_client.delete("/v1/budgets/trash/%s/" % budget.pk)
    assert response.status_code == 204
    assert Budget.objects.first() is None


def test_get_budget_items(api_client, user, create_budget,
        create_budget_account, create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(budget=budget, identifier="Account A")
    create_budget_subaccount(budget=budget, parent=account, identifier="Jack")
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


def test_get_budget_items_tree(api_client, user, create_budget,
        create_budget_account, create_budget_subaccount):
    budget = create_budget()
    accounts = [
        create_budget_account(budget=budget, identifier="Account A"),
        create_budget_account(budget=budget, identifier="Account B"),
    ]
    subaccounts = [
        [
            create_budget_subaccount(
                budget=budget,
                parent=accounts[0],
                identifier="Sub Account A-A"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=accounts[0],
                identifier="Sub Account A-B"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=accounts[0],
                identifier="Sub Account A-C"
            )
        ],
        [
            create_budget_subaccount(
                budget=budget,
                parent=accounts[1],
                identifier="Sub Account B-A"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=accounts[1],
                identifier="Sub Account B-B"
            ),
            create_budget_subaccount(
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
                    "name": subaccounts[0][0].name,
                    "description": subaccounts[0][0].description,
                    "children": []
                },
                {
                    "id": subaccounts[0][1].pk,
                    "identifier": "Sub Account A-B",
                    "type": "subaccount",
                    "name": subaccounts[0][1].name,
                    "description": subaccounts[0][1].description,
                    "children": []
                },
                {
                    "id": subaccounts[0][2].pk,
                    "identifier": "Sub Account A-C",
                    "type": "subaccount",
                    "name": subaccounts[0][2].name,
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
                    "name": subaccounts[1][0].name,
                    "description": subaccounts[1][0].description,
                    "children": []
                },
                {
                    "id": subaccounts[1][1].pk,
                    "identifier": "Sub Account B-B",
                    "type": "subaccount",
                    "name": subaccounts[1][1].name,
                    "description": subaccounts[1][1].description,
                    "children": []
                },
                {
                    "id": subaccounts[1][2].pk,
                    "identifier": "Sub Account B-C",
                    "type": "subaccount",
                    "name": subaccounts[1][2].name,
                    "description": subaccounts[1][2].description,
                    "children": []
                }
            ]
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_accounts(api_client, user, create_budget,
        create_budget_account):
    api_client.force_login(user)
    budget = create_budget()
    accounts = [
        create_budget_account(budget=budget),
        create_budget_account(budget=budget)
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
        create_budget, create_budget_account):
    api_client.force_login(user)
    budget = create_budget()
    another_budget = create_budget()
    accounts = [
        create_budget_account(budget=budget),
        create_budget_account(budget=another_budget)
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
        create_budget_account, create_actual):
    api_client.force_login(user)
    budget = create_budget()
    account = create_budget_account(budget=budget)
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


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_budget_fringes(api_client, user, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.patch(
        "/v1/budgets/%s/bulk-create-fringes/" % budget.pk,
        format='json',
        data={
            'data': [
                {
                    'name': 'fringe-a',
                    'rate': 1.2,
                },
                {
                    'name': 'fringe-b',
                    'rate': 2.2,
                }
            ]
        })
    assert response.status_code == 201

    fringes = Fringe.objects.all()
    assert len(fringes) == 2
    assert fringes[0].name == "fringe-a"
    assert fringes[0].rate == 1.2
    assert fringes[0].budget == budget
    assert fringes[1].name == "fringe-b"
    assert fringes[1].rate == 2.2
    assert fringes[1].budget == budget

    assert response.json()['data'][0]['name'] == 'fringe-a'
    assert response.json()['data'][0]['rate'] == 1.2
    assert response.json()['data'][1]['name'] == 'fringe-b'
    assert response.json()['data'][1]['rate'] == 2.2


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_fringes(api_client, user, create_budget,
        create_fringe):
    api_client.force_login(user)
    budget = create_budget()
    fringes = [
        create_fringe(budget=budget),
        create_fringe(budget=budget)
    ]
    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-fringes/" % budget.pk,
        format='json',
        data={
            'data': [
                {
                    'id': fringes[0].pk,
                    'name': 'New Name 1',
                },
                {
                    'id': fringes[1].pk,
                    'name': 'New Name 2',
                }
            ]
        })
    assert response.status_code == 200

    fringes[0].refresh_from_db()
    assert fringes[0].name == "New Name 1"
    fringes[1].refresh_from_db()
    assert fringes[1].name == "New Name 2"


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_fringes_name_not_unique(api_client, user,
        create_budget, create_fringe):
    api_client.force_login(user)
    budget = create_budget()
    create_fringe(budget=budget, name='Non-Unique Name')
    fringes = [
        create_fringe(budget=budget),
        create_fringe(budget=budget)
    ]
    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-fringes/" % budget.pk,
        format='json',
        data={
            'data': [
                {
                    'id': fringes[0].pk,
                    'name': 'New Name 1',
                },
                {
                    'id': fringes[1].pk,
                    'name': 'Non-Unique Name',
                }
            ]
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_fringes_name_not_unique_in_update(api_client, user,
        create_budget, create_fringe):
    api_client.force_login(user)
    budget = create_budget()
    fringes = [
        create_fringe(budget=budget, name='Non-Unique Name'),
        create_fringe(budget=budget)
    ]
    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-fringes/" % budget.pk,
        format='json',
        data={
            'data': [
                {
                    'id': fringes[0].pk,
                    'rate': 5.1,
                },
                {
                    'id': fringes[1].pk,
                    'name': 'Non-Unique Name',
                }
            ]
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_fringes_name_will_be_unique(api_client, user,
        create_budget, create_fringe):
    api_client.force_login(user)
    budget = create_budget()
    fringes = [
        create_fringe(budget=budget, name='Non-Unique Name'),
        create_fringe(budget=budget)
    ]
    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-fringes/" % budget.pk,
        format='json',
        data={
            'data': [
                {
                    'id': fringes[0].pk,
                    'name': 'New Name',
                },
                {
                    'id': fringes[1].pk,
                    'name': 'Non-Unique Name',
                }
            ]
        })
    assert response.status_code == 200
