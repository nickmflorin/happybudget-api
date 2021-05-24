import datetime
from datetime import timezone
import mock
import pytest

from greenbudget.app.group.models import (
    BudgetSubAccountGroup, TemplateSubAccountGroup)
from greenbudget.app.subaccount.models import (
    BudgetSubAccount, TemplateSubAccount)


@pytest.mark.freeze_time('2020-01-01')
def test_unit_properly_serializes(api_client, user, create_budget_subaccount,
        create_budget_account, create_budget, create_subaccount_unit):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    unit = create_subaccount_unit()
    subaccount = create_budget_subaccount(
        parent=account,
        budget=budget,
        unit=unit
    )
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['unit'] == {
        'id': unit.pk,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        'title': unit.title,
        'order': unit.order,
        'color': unit.color.code
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_subaccount_unit(api_client, user, create_budget_subaccount,
        create_budget_account, create_budget, create_subaccount_unit):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(
        parent=account,
        name="Original Name",
        description="Original Description",
        identifier="Original identifier",
        budget=budget
    )
    unit = create_subaccount_unit()
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "unit": unit.pk
    })
    assert response.status_code == 200
    subaccount.refresh_from_db()
    assert response.json()['unit'] == {
        'id': unit.pk,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        'title': unit.title,
        'order': unit.order,
        'color': unit.color.code
    }
    assert subaccount.unit == unit


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_subaccount(api_client, user, create_budget_subaccount,
        create_budget_account, create_budget):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)

    api_client.force_login(user)
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
        "rate": subaccount.rate,
        "multiplier": subaccount.multiplier,
        "type": "subaccount",
        "object_id": account.pk,
        "budget": budget.pk,
        "parent_type": "account",
        "account": account.pk,
        "actual": None,
        "estimated": None,
        "variance": None,
        "subaccounts": [],
        "fringes": [],
        "siblings": [],
        "group": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "unit": None,
        "ancestors": [
            {
                "type": "budget",
                "id": budget.pk,
                "name": budget.name
            },
            {
                "id": account.id,
                "type": "account",
                "identifier": account.identifier,
                "description": account.description
            }
        ]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_subaccount(api_client, user, create_template_subaccount,
        create_template_account, create_template):
    template = create_template()
    account = create_template_account(budget=template)
    subaccount = create_template_subaccount(parent=account, budget=template)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": subaccount.pk,
        "name": subaccount.name,
        "identifier": subaccount.identifier,
        "description": subaccount.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": subaccount.quantity,
        "rate": subaccount.rate,
        "multiplier": subaccount.multiplier,
        "type": "subaccount",
        "object_id": account.pk,
        "budget": template.pk,
        "parent_type": "account",
        "account": account.pk,
        "estimated": None,
        "subaccounts": [],
        "fringes": [],
        "siblings": [],
        "group": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "unit": None,
        "ancestors": [
            {
                "type": "template",
                "id": template.pk,
                "name": template.name
            },
            {
                "id": account.id,
                "type": "account",
                "identifier": account.identifier,
                "description": account.description
            }
        ]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget_subaccount(api_client, user, create_budget_subaccount,
        create_budget_account, create_budget):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(
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
        "rate": 1.5,
        "multiplier": subaccount.multiplier,
        "type": "subaccount",
        "object_id": account.pk,
        "budget": budget.pk,
        "parent_type": "account",
        "account": account.pk,
        "estimated": 15.0,
        "actual": None,
        "variance": None,
        "subaccounts": [],
        "fringes": [],
        "siblings": [],
        "group": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "unit": None,
        "ancestors": [
            {
                "type": "budget",
                "id": budget.pk,
                "name": budget.name,
            },
            {
                "id": account.id,
                "type": "account",
                "identifier": account.identifier,
                "description": account.description
            }
        ]
    }
    assert subaccount.name == "New Name"
    assert subaccount.description == "New Description"
    assert subaccount.identifier == "New identifier"
    assert subaccount.quantity == 10
    assert subaccount.rate == 1.5


@pytest.mark.freeze_time('2020-01-01')
def test_update_template_subaccount(api_client, user, create_template_account,
        create_template_subaccount, create_template):
    template = create_template()
    account = create_template_account(budget=template)
    subaccount = create_template_subaccount(
        parent=account,
        name="Original Name",
        description="Original Description",
        identifier="Original identifier",
        budget=template
    )
    api_client.force_login(user)
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
        "rate": 1.5,
        "multiplier": subaccount.multiplier,
        "type": "subaccount",
        "object_id": account.pk,
        "budget": template.pk,
        "parent_type": "account",
        "account": account.pk,
        "estimated": 15.0,
        "subaccounts": [],
        "fringes": [],
        "siblings": [],
        "group": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "unit": None,
        "ancestors": [
            {
                "type": "template",
                "id": template.pk,
                "name": template.name,
            },
            {
                "id": account.id,
                "type": "account",
                "identifier": account.identifier,
                "description": account.description
            }
        ]
    }
    assert subaccount.name == "New Name"
    assert subaccount.description == "New Description"
    assert subaccount.identifier == "New identifier"
    assert subaccount.quantity == 10
    assert subaccount.rate == 1.5


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_subaccount_subaccounts(api_client, user, create_budget,
        create_budget_subaccount, create_budget_account):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    parent = create_budget_subaccount(parent=account, budget=budget)
    another_parent = create_budget_subaccount(parent=account, budget=budget)
    subaccounts = [
        create_budget_subaccount(parent=parent, budget=budget, identifier='A'),
        create_budget_subaccount(parent=parent, budget=budget, identifier='B'),
        create_budget_subaccount(
            parent=another_parent,
            budget=budget,
            identifier='C'
        )
    ]
    api_client.force_login(user)
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
            "rate": subaccounts[0].rate,
            "multiplier": subaccounts[0].multiplier,
            "type": "subaccount",
            "object_id": parent.pk,
            "budget": budget.pk,
            "parent_type": "subaccount",
            "account": parent.account.pk,
            "actual": None,
            "estimated": None,
            "variance": None,
            "subaccounts": [],
            "fringes": [],
            "group": None,
            "created_by": user.pk,
            "updated_by": user.pk,
            "unit": None,
            "ancestors": [
                {
                    "type": "budget",
                    "id": budget.pk,
                    "name": budget.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "identifier": account.identifier,
                    "description": account.description,
                },
                {
                    "id": parent.id,
                    "type": "subaccount",
                    "identifier": parent.identifier,
                    "name": parent.name,
                    "description": parent.description,
                }
            ],
            "siblings": [{
                "id": subaccounts[1].id,
                "type": "subaccount",
                "identifier": subaccounts[1].identifier,
                "name": subaccounts[1].name,
                "description": subaccounts[1].description
            }]
        },
        {
            "id": subaccounts[1].pk,
            "name": subaccounts[1].name,
            "identifier": "%s" % subaccounts[1].identifier,
            "description": subaccounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[1].quantity,
            "rate": subaccounts[1].rate,
            "multiplier": subaccounts[1].multiplier,
            "type": "subaccount",
            "object_id": parent.pk,
            "budget": budget.pk,
            "parent_type": "subaccount",
            "account": parent.account.pk,
            "actual": None,
            "estimated": None,
            "variance": None,
            "subaccounts": [],
            "fringes": [],
            "group": None,
            "created_by": user.pk,
            "updated_by": user.pk,
            "unit": None,
            "ancestors": [
                {
                    "type": "budget",
                    "id": budget.pk,
                    "name": budget.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "identifier": account.identifier,
                    "description": account.description,
                },
                {
                    "id": parent.id,
                    "type": "subaccount",
                    "identifier": parent.identifier,
                    "name": parent.name,
                    "description": parent.description,
                }
            ],
            "siblings": [{
                "id": subaccounts[0].id,
                "type": "subaccount",
                "identifier": subaccounts[0].identifier,
                "name": subaccounts[0].name,
                "description": subaccounts[0].description
            }],
        },
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_subaccount_subaccounts(api_client, user, create_template,
        create_template_subaccount, create_template_account):
    template = create_template()
    account = create_template_account(budget=template)
    parent = create_template_subaccount(parent=account, budget=template)
    another_parent = create_template_subaccount(parent=account, budget=template)
    subaccounts = [
        create_template_subaccount(
            parent=parent,
            budget=template,
            identifier='A'
        ),
        create_template_subaccount(
            parent=parent,
            budget=template,
            identifier='B'
        ),
        create_template_subaccount(
            parent=another_parent,
            budget=template,
            identifier='C'
        )
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % parent.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": subaccounts[0].pk,
            "name": subaccounts[0].name,
            "identifier": subaccounts[0].identifier,
            "description": subaccounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[0].quantity,
            "rate": subaccounts[0].rate,
            "multiplier": subaccounts[0].multiplier,
            "type": "subaccount",
            "object_id": parent.pk,
            "budget": template.pk,
            "parent_type": "subaccount",
            "account": parent.account.pk,
            "estimated": None,
            "subaccounts": [],
            "fringes": [],
            "group": None,
            "created_by": user.pk,
            "updated_by": user.pk,
            "unit": None,
            "ancestors": [
                {
                    "type": "template",
                    "id": template.pk,
                    "name": template.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "identifier": account.identifier,
                    "description": account.description,
                },
                {
                    "id": parent.id,
                    "type": "subaccount",
                    "identifier": parent.identifier,
                    "name": parent.name,
                    "description": parent.description,
                }
            ],
            "siblings": [{
                "id": subaccounts[1].id,
                "type": "subaccount",
                "identifier": subaccounts[1].identifier,
                "name": subaccounts[1].name,
                "description": subaccounts[1].description,
            }]
        },
        {
            "id": subaccounts[1].pk,
            "name": subaccounts[1].name,
            "identifier": "%s" % subaccounts[1].identifier,
            "description": subaccounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[1].quantity,
            "rate": subaccounts[1].rate,
            "multiplier": subaccounts[1].multiplier,
            "type": "subaccount",
            "object_id": parent.pk,
            "budget": template.pk,
            "parent_type": "subaccount",
            "account": parent.account.pk,
            "estimated": None,
            "subaccounts": [],
            "fringes": [],
            "group": None,
            "created_by": user.pk,
            "updated_by": user.pk,
            "unit": None,
            "ancestors": [
                {
                    "type": "template",
                    "id": template.pk,
                    "name": template.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "identifier": account.identifier,
                    "description": account.description,
                },
                {
                    "id": parent.id,
                    "type": "subaccount",
                    "identifier": parent.identifier,
                    "name": parent.name,
                    "description": parent.description,
                }
            ],
            "siblings": [{
                "id": subaccounts[0].id,
                "type": "subaccount",
                "identifier": subaccounts[0].identifier,
                "name": subaccounts[0].name,
                "description": subaccounts[0].description,
            }],
        },
    ]


def test_remove_budget_subaccount_from_group(api_client, user, create_budget,
        create_budget_subaccount, create_budget_account,
        create_budget_subaccount_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    group = create_budget_subaccount_group(parent=account)
    subaccount = create_budget_subaccount(
        parent=account,
        budget=budget,
        group=group
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk,
        format='json',
        data={
            "group": None,
        }
    )
    assert response.status_code == 200
    subaccount.refresh_from_db()
    assert subaccount.group is None

    assert BudgetSubAccountGroup.objects.first() is None


def test_remove_template_subaccount_from_group(api_client, user,
        create_template, create_template_subaccount, create_template_account,
        create_template_subaccount_group):
    template = create_template()
    account = create_template_account(budget=template)
    group = create_template_subaccount_group(parent=account)
    subaccount = create_template_subaccount(
        parent=account,
        budget=template,
        group=group
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk,
        format='json',
        data={
            "group": None,
        }
    )
    assert response.status_code == 200
    subaccount.refresh_from_db()
    assert subaccount.group is None

    assert TemplateSubAccountGroup.objects.first() is None


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_subaccount_subaccounts(api_client, user,
        create_budget, create_budget_account, create_budget_subaccount,
        freezer):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(
        parent=account, budget=budget, identifier="subaccount-a")
    subaccounts = [
        create_budget_subaccount(budget=budget, parent=subaccount),
        create_budget_subaccount(budget=budget, parent=subaccount)
    ]
    api_client.force_login(user)
    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-update-subaccounts/" % subaccount.pk,
        format='json',
        data={
            'data': [
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
    assert response.status_code == 200
    assert response.json()['subaccounts'][0] == subaccounts[0].id
    assert response.json()['subaccounts'][1] == subaccounts[1].id

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].name == "New Name 1"
    subaccounts[1].refresh_from_db()
    assert subaccounts[1].name == "New Name 2"

    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)


def test_bulk_update_budget_subaccount_subaccounts_budget_updated_once(
        api_client, user, create_budget, create_budget_account,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(
        parent=account, budget=budget, identifier="subaccount-a")
    subaccounts = [
        create_budget_subaccount(budget=budget, parent=subaccount),
        create_budget_subaccount(budget=budget, parent=subaccount)
    ]
    api_client.force_login(user)
    with mock.patch('greenbudget.app.budget.models.BaseBudget.save') as save:
        response = api_client.patch(
            "/v1/subaccounts/%s/bulk-update-subaccounts/" % subaccount.pk,
            format='json',
            data={
                'data': [
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
    assert response.status_code == 200
    assert save.call_count == 1


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_template_subaccount_subaccounts(api_client, user,
        create_template, create_template_account, create_template_subaccount,
        freezer):
    template = create_template()
    account = create_template_account(budget=template)
    subaccount = create_template_subaccount(
        parent=account, budget=template, identifier="subaccount-a")
    subaccounts = [
        create_template_subaccount(budget=template, parent=subaccount),
        create_template_subaccount(budget=template, parent=subaccount)
    ]
    api_client.force_login(user)
    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-update-subaccounts/" % subaccount.pk,
        format='json',
        data={
            'data': [
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
    assert response.status_code == 200
    assert response.json()['subaccounts'][0] == subaccounts[0].id
    assert response.json()['subaccounts'][1] == subaccounts[1].id

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].name == "New Name 1"
    subaccounts[1].refresh_from_db()
    assert subaccounts[1].name == "New Name 2"

    template.refresh_from_db()
    assert template.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)


def test_bulk_update_template_subaccount_subaccounts_template_updated_once(
        api_client, user, create_template, create_template_account,
        create_template_subaccount):
    template = create_template()
    account = create_template_account(budget=template)
    subaccount = create_template_subaccount(
        parent=account, budget=template, identifier="subaccount-a")
    subaccounts = [
        create_template_subaccount(budget=template, parent=subaccount),
        create_template_subaccount(budget=template, parent=subaccount)
    ]
    api_client.force_login(user)
    with mock.patch('greenbudget.app.budget.models.BaseBudget.save') as save:
        response = api_client.patch(
            "/v1/subaccounts/%s/bulk-update-subaccounts/" % subaccount.pk,
            format='json',
            data={
                'data': [
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
    assert response.status_code == 200
    assert save.call_count == 1


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_budget_subaccount_subaccounts(api_client, user,
        create_budget, create_budget_account, create_budget_subaccount,
        freezer):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)
    api_client.force_login(user)

    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-create-subaccounts/" % subaccount.pk,
        format='json',
        data={
            'data': [
                {
                    'identifier': 'subaccount-a',
                    'name': 'New Name 1',
                },
                {
                    'identifier': 'subaccount-b',
                    'name': 'New Name 2',
                }
            ]
        })
    assert response.status_code == 201

    subaccounts = BudgetSubAccount.objects.all()
    assert len(subaccounts) == 3
    assert subaccounts[1].identifier == "subaccount-a"
    assert subaccounts[1].name == "New Name 1"
    assert subaccounts[1].budget == budget
    assert subaccounts[1].parent == subaccount
    assert subaccounts[2].name == "New Name 2"
    assert subaccounts[2].identifier == "subaccount-b"
    assert subaccounts[2].budget == budget
    assert subaccounts[2].parent == subaccount

    assert response.json()['data'][0]['identifier'] == 'subaccount-a'
    assert response.json()['data'][0]['name'] == 'New Name 1'
    assert response.json()['data'][1]['identifier'] == 'subaccount-b'
    assert response.json()['data'][1]['name'] == 'New Name 2'

    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_budget_subaccount_subaccounts_count(api_client, user,
        create_budget, create_budget_account, create_budget_subaccount,
        freezer):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)
    api_client.force_login(user)

    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-create-subaccounts/" % subaccount.pk,
        format='json',
        data={'count': 2}
    )
    assert response.status_code == 201

    subaccounts = BudgetSubAccount.objects.all()
    assert len(subaccounts) == 3
    assert len(response.json()['data']) == 2

    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_template_subaccount_subaccounts(api_client, user,
        create_template, create_template_account, create_template_subaccount,
        freezer):
    template = create_template()
    account = create_template_account(budget=template)
    subaccount = create_template_subaccount(parent=account, budget=template)
    api_client.force_login(user)

    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-create-subaccounts/" % subaccount.pk,
        format='json',
        data={
            'data': [
                {
                    'identifier': 'subaccount-a',
                    'name': 'New Name 1',
                },
                {
                    'identifier': 'subaccount-b',
                    'name': 'New Name 2',
                }
            ]
        })
    assert response.status_code == 201

    subaccounts = TemplateSubAccount.objects.all()
    assert len(subaccounts) == 3
    assert subaccounts[1].identifier == "subaccount-a"
    assert subaccounts[1].name == "New Name 1"
    assert subaccounts[1].budget == template
    assert subaccounts[1].parent == subaccount
    assert subaccounts[2].name == "New Name 2"
    assert subaccounts[2].identifier == "subaccount-b"
    assert subaccounts[2].budget == template
    assert subaccounts[2].parent == subaccount

    assert response.json()['data'][0]['identifier'] == 'subaccount-a'
    assert response.json()['data'][0]['name'] == 'New Name 1'
    assert response.json()['data'][1]['identifier'] == 'subaccount-b'
    assert response.json()['data'][1]['name'] == 'New Name 2'

    template.refresh_from_db()
    assert template.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_template_subaccount_subaccounts_count(api_client, user,
        create_template, create_template_account, create_template_subaccount,
        freezer):
    template = create_template()
    account = create_template_account(budget=template)
    subaccount = create_template_subaccount(parent=account, budget=template)
    api_client.force_login(user)

    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-create-subaccounts/" % subaccount.pk,
        format='json',
        data={'count': 2}
    )
    assert response.status_code == 201

    subaccounts = TemplateSubAccount.objects.all()
    assert len(subaccounts) == 3
    assert len(response.json()['data']) == 2

    template.refresh_from_db()
    assert template.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)
