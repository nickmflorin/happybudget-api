from copy import deepcopy
import pytest

from greenbudget.app.history.models import FieldAlterationEvent
from greenbudget.app.subaccount.models import SubAccount


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount(api_client, user, create_sub_account, create_account,
        create_budget):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(parent=account, budget=budget)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": subaccount.pk,
        "name": subaccount.name,
        "identifier": "%s" % subaccount.identifier,
        "description": subaccount.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": subaccount.quantity,
        "rate": "{:.2f}".format(subaccount.rate),
        "multiplier": "{:.2f}".format(subaccount.multiplier),
        "unit": subaccount.unit,
        "unit_name": subaccount.unit_name,
        "type": "subaccount",
        "object_id": account.pk,
        "budget": budget.pk,
        "parent_type": "account",
        "account": account.pk,
        "actual": None,
        "estimated": None,
        "variance": None,
        "subaccounts": [],
        "ancestors": [
            {
                "id": budget.id,
                "type": "budget",
                "identifier": budget.name,
            },
            {
                "id": account.id,
                "type": "account",
                "identifier": '%s' % account.identifier,
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
        data={
            'name': 'New Subaccount',
            'identifier': '100',
            'description': 'Test'
        }
    )
    assert response.status_code == 201
    subaccount = SubAccount.objects.first()
    assert subaccount.name == "New Subaccount"
    assert subaccount.description == "Test"
    assert subaccount.identifier == "100"

    assert subaccount is not None
    assert response.json() == {
        "id": subaccount.pk,
        "name": 'New Subaccount',
        "identifier": '100',
        "description": 'Test',
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": None,
        "rate": None,
        "multiplier": None,
        "unit": None,
        "unit_name": '',
        "type": "subaccount",
        "object_id": account.pk,
        "budget": budget.pk,
        "parent_type": "account",
        "account": account.pk,
        "actual": None,
        "estimated": None,
        "variance": None,
        "subaccounts": [],
        "ancestors": [
            {
                "id": budget.id,
                "type": "budget",
                "identifier": budget.name,
            },
            {
                "id": account.id,
                "type": "account",
                "identifier": '%s' % account.identifier,
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
def test_create_subaccount_duplicate_identifier(api_client, user,
        create_account, create_budget, create_sub_account):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    create_sub_account(
        parent=account, identifier="identifier Number", budget=budget)
    response = api_client.post(
        "/v1/budgets/%s/accounts/%s/subaccounts/" % (budget.pk, account.pk),
        data={'name': 'New Subaccount', 'identifier': 'identifier Number'}
    )
    assert response.status_code == 400
    assert response.json() == {
        'errors': {
            'identifier': [{
                'message': 'The fields identifier must make a unique set.',
                'code': 'unique'
            }]
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_subaccount(api_client, user, create_sub_account, create_account,
        create_budget):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(
        parent=account,
        name="Original Name",
        description="Original Description",
        identifier="Original identifier",
        budget=budget
    )
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "name": "New Name",
        "description": "New Description",
        "identifier": "New identifier",
        "quantity": 10,
        "rate": 1.5
    })
    assert response.status_code == 200
    subaccount.refresh_from_db()
    assert response.json() == {
        "id": subaccount.pk,
        "name": "New Name",
        "identifier": "New identifier",
        "description": "New Description",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": 10,
        "rate": "1.50",
        "multiplier": "{:.2f}".format(subaccount.multiplier),
        "unit": subaccount.unit,
        "unit_name": subaccount.unit_name,
        "type": "subaccount",
        "object_id": account.pk,
        "budget": budget.pk,
        "parent_type": "account",
        "account": account.pk,
        "estimated": '15.00',
        "actual": None,
        "variance": None,
        "subaccounts": [],
        "ancestors": [
            {
                "id": budget.id,
                "type": "budget",
                "identifier": budget.name,
            },
            {
                "id": account.id,
                "type": "account",
                "identifier": '%s' % account.identifier,
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
    assert subaccount.identifier == "New identifier"
    assert subaccount.quantity == 10
    assert subaccount.rate == 1.5


@pytest.mark.freeze_time('2020-01-01')
def test_update_subaccount_duplicate_identifier(api_client, user,
        create_account, create_budget, create_sub_account):
    api_client.force_login(user)
    budget = create_budget()
    accounts = [
        create_account(budget=budget),
        create_account(budget=budget)
    ]
    create_sub_account(
        parent=accounts[0], identifier="Identifier", budget=budget)
    sub_account = create_sub_account(
        parent=accounts[1], identifier="Identifier 2", budget=budget)
    response = api_client.patch(
        "/v1/subaccounts/%s/" % (sub_account.pk),
        data={'identifier': 'Identifier'}
    )
    assert response.status_code == 400
    assert response.json() == {
        'errors': {
            'identifier': [{
                'message': 'The fields identifier must make a unique set.',
                'code': 'unique'
            }]
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_account_subaccounts(api_client, user, create_account,
        create_budget, create_sub_account):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    another_account = create_account(budget=budget)
    subaccounts = [
        create_sub_account(parent=account, budget=budget),
        create_sub_account(parent=account, budget=budget),
        create_sub_account(parent=another_account, budget=budget)
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
            "identifier": "%s" % subaccounts[0].identifier,
            "description": subaccounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[0].quantity,
            "rate": "{:.2f}".format(subaccounts[0].rate),
            "multiplier": "{:.2f}".format(subaccounts[0].multiplier),
            "unit": subaccounts[0].unit,
            "unit_name": subaccounts[0].unit_name,
            "type": "subaccount",
            "object_id": account.pk,
            "budget": budget.pk,
            "parent_type": "account",
            "account": account.pk,
            "actual": None,
            "estimated": None,
            "variance": None,
            "subaccounts": [],
            "ancestors": [
                {
                    "id": budget.id,
                    "type": "budget",
                    "identifier": budget.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "identifier": '%s' % account.identifier,
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
            "identifier": "%s" % subaccounts[1].identifier,
            "description": subaccounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[1].quantity,
            "rate": "{:.2f}".format(subaccounts[1].rate),
            "multiplier": "{:.2f}".format(subaccounts[1].multiplier),
            "unit": subaccounts[1].unit,
            "unit_name": subaccounts[1].unit_name,
            "type": "subaccount",
            "object_id": account.pk,
            "budget": budget.pk,
            "parent_type": "account",
            "account": account.pk,
            "actual": None,
            "estimated": None,
            "variance": None,
            "subaccounts": [],
            "ancestors": [
                {
                    "id": budget.id,
                    "type": "budget",
                    "identifier": budget.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "identifier": '%s' % account.identifier,
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
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount_subaccounts(api_client, user, create_sub_account,
        create_budget, create_account):

    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    parent = create_sub_account(parent=account, budget=budget)
    another_parent = create_sub_account(parent=account, budget=budget)
    subaccounts = [
        create_sub_account(parent=parent, budget=budget),
        create_sub_account(parent=parent, budget=budget),
        create_sub_account(parent=another_parent, budget=budget)
    ]
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % parent.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": subaccounts[0].pk,
            "name": subaccounts[0].name,
            "identifier": "%s" % subaccounts[0].identifier,
            "description": subaccounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[0].quantity,
            "rate": "{:.2f}".format(subaccounts[0].rate),
            "multiplier": "{:.2f}".format(subaccounts[0].multiplier),
            "unit": subaccounts[0].unit,
            "unit_name": subaccounts[0].unit_name,
            "type": "subaccount",
            "object_id": parent.pk,
            "budget": budget.pk,
            "parent_type": "subaccount",
            "account": parent.account.pk,
            "actual": None,
            "estimated": None,
            "variance": None,
            "subaccounts": [],
            "ancestors": [
                {
                    "id": budget.id,
                    "type": "budget",
                    "identifier": budget.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "identifier": '%s' % account.identifier,
                },
                {
                    "id": parent.id,
                    "type": "subaccount",
                    "identifier": "%s" % parent.identifier,
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
            "identifier": "%s" % subaccounts[1].identifier,
            "description": subaccounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[1].quantity,
            "rate": "{:.2f}".format(subaccounts[1].rate),
            "multiplier": "{:.2f}".format(subaccounts[1].multiplier),
            "unit": subaccounts[1].unit,
            "unit_name": subaccounts[1].unit_name,
            "type": "subaccount",
            "object_id": parent.pk,
            "budget": budget.pk,
            "parent_type": "subaccount",
            "account": parent.account.pk,
            "actual": None,
            "estimated": None,
            "variance": None,
            "subaccounts": [],
            "ancestors": [
                {
                    "id": budget.id,
                    "type": "budget",
                    "identifier": budget.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "identifier": '%s' % account.identifier,
                },
                {
                    "id": parent.id,
                    "type": "subaccount",
                    "identifier": "%s" % parent.identifier,
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
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_account_subaccounts_history(api_client, create_budget, user,
        create_sub_account, create_account):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(
        parent=account,
        name="Original Name",
        description="Original Description",
        identifier="Original identifier",
        budget=budget
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "name": "New Name",
        "description": "New Description",
        "identifier": "New identifier",
        "quantity": 10,
        "rate": 1.5
    })
    response = api_client.get(
        "/v1/budgets/%s/accounts/%s/subaccounts/history/"
        % (budget.pk, account.pk)
    )
    assert response.status_code == 200

    assert FieldAlterationEvent.objects.count() == 5

    assert response.json()['count'] == 5
    serialized_events = [
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New Description",
            "old_value": "Original Description",
            "field": "description",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New identifier",
            "old_value": "Original identifier",
            "field": "identifier",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "1.50",
            "old_value": "{:.2f}".format(subaccount.rate),
            "field": "rate",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New Name",
            "old_value": "Original Name",
            "field": "name",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "10",
            "old_value": None,
            "field": "quantity",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        }
    ]
    for serialized_event in response.json()['data']:
        event_without_id = deepcopy(serialized_event)
        del event_without_id['id']
        assert event_without_id in serialized_events


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount_subaccounts_history(api_client, create_budget, user,
        create_sub_account, create_account):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    parent_subaccount = create_sub_account(parent=account, budget=budget)
    subaccount = create_sub_account(
        parent=parent_subaccount,
        name="Original Name",
        description="Original Description",
        identifier="Original identifier",
        budget=budget
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "name": "New Name",
        "description": "New Description",
        "identifier": "New identifier",
        "quantity": 10,
        "rate": 1.5
    })
    response = api_client.get(
        "/v1/subaccounts/%s/subaccounts/history/"
        % parent_subaccount.pk
    )
    assert response.status_code == 200
    assert FieldAlterationEvent.objects.count() == 5

    assert response.json()['count'] == 5
    serialized_events = [
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New Description",
            "old_value": "Original Description",
            "field": "description",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New identifier",
            "old_value": "Original identifier",
            "field": "identifier",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "1.50",
            "old_value": "{:.2f}".format(subaccount.rate),
            "field": "rate",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New Name",
            "old_value": "Original Name",
            "field": "name",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "10",
            "old_value": None,
            "field": "quantity",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        }
    ]
    for serialized_event in response.json()['data']:
        event_without_id = deepcopy(serialized_event)
        del event_without_id['id']
        assert event_without_id in serialized_events


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount_history(api_client, create_budget, create_account,
        create_sub_account, user):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(
        parent=account,
        name="Original Name",
        description="Original Description",
        identifier="Original identifier",
        budget=budget
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "name": "New Name",
        "description": "New Description",
        "identifier": "New identifier",
        "quantity": 10,
        "rate": 1.5
    })
    response = api_client.get("/v1/subaccounts/%s/history/" % subaccount.pk)
    assert response.status_code == 200

    assert FieldAlterationEvent.objects.count() == 5

    assert response.json()['count'] == 5
    serialized_events = [
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New Description",
            "old_value": "Original Description",
            "field": "description",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New identifier",
            "old_value": "Original identifier",
            "field": "identifier",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "1.50",
            "old_value": "{:.2f}".format(subaccount.rate),
            "field": "rate",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New Name",
            "old_value": "Original Name",
            "field": "name",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "10",
            "old_value": None,
            "field": "quantity",
            "object_id": subaccount.pk,
            "content_object_type": "subaccount",
            "type": "field_alteration",
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email
            }
        }
    ]
    for serialized_event in response.json()['data']:
        event_without_id = deepcopy(serialized_event)
        del event_without_id['id']
        assert event_without_id in serialized_events
