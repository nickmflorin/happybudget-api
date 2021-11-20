import datetime
from datetime import timezone
import mock
import pytest


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_unit_properly_serializes(api_client, user, create_subaccount,
        create_account, create_context_budget, create_subaccount_unit, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    unit = create_subaccount_unit()
    subaccount = create_subaccount(
        parent=account,
        unit=unit,
        context=context
    )
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['unit'] == {
        'id': unit.pk,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        'title': unit.title,
        'plural_title': unit.plural_title,
        'order': unit.order,
        'color': unit.color.code
    }


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_subaccount_unit(api_client, user, create_subaccount, context,
        create_account, create_context_budget, create_subaccount_unit):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
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
        'plural_title': unit.plural_title,
        'order': unit.order,
        'color': unit.color.code
    }
    assert subaccount.unit == unit


@pytest.mark.parametrize('context', ['budget'])
def test_update_subaccount_contact(api_client, user, create_subaccount,
        create_account, create_context_budget, create_contact, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    contact = create_contact(created_by=user)
    subaccount = create_subaccount(parent=account, context=context)
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "contact": contact.pk
    })
    assert response.status_code == 200
    subaccount.refresh_from_db()
    assert response.json()['contact'] == contact.pk
    assert subaccount.contact == contact


@pytest.mark.parametrize('context', ['budget'])
def test_update_subaccount_contact_wrong_user(api_client, user, admin_user,
        create_subaccount, create_account, create_context_budget, context,
        create_contact):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    contact = create_contact(created_by=admin_user)
    subaccount = create_subaccount(parent=account, context=context)
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "contact": contact.pk
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget'])
def test_get_subaccount(api_client, user, create_subaccount, create_account,
        create_context_budget, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": subaccount.pk,
        "identifier": "%s" % subaccount.identifier,
        "description": subaccount.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": subaccount.quantity,
        "rate": subaccount.rate,
        "multiplier": subaccount.multiplier,
        "type": "subaccount",
        "object_id": account.pk,
        "parent_type": "account",
        "nominal_value": 0.0,
        "fringe_contribution": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "fringes": [],
        "siblings": [],
        "created_by": user.pk,
        "updated_by": user.pk,
        "unit": None,
        "contact": None,
        "attachments": [],
        "ancestors": [
            {
                "type": "budget",
                "id": budget.pk,
                "name": budget.name,
                "domain": context,
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
@pytest.mark.parametrize('context', ['template'])
def test_get_template_subaccount(api_client, user, create_subaccount, context,
        create_account, create_context_budget):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": subaccount.pk,
        "identifier": "%s" % subaccount.identifier,
        "description": subaccount.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": subaccount.quantity,
        "rate": subaccount.rate,
        "multiplier": subaccount.multiplier,
        "type": "subaccount",
        "object_id": account.pk,
        "parent_type": "account",
        "nominal_value": 0.0,
        "fringe_contribution": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "fringes": [],
        "siblings": [],
        "created_by": user.pk,
        "updated_by": user.pk,
        "unit": None,
        "ancestors": [
            {
                "type": "budget",
                "id": budget.pk,
                "name": budget.name,
                "domain": context,
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
@pytest.mark.parametrize('context', ['budget'])
def test_update_subaccount(api_client, user, create_subaccount, create_account,
        create_context_budget, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(
        parent=account,
        description="Original Description",
        identifier="Original identifier",
        context=context
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "description": "New Description",
        "identifier": "New identifier",
        "quantity": 10,
        "rate": 1.5
    })
    assert response.status_code == 200
    subaccount.refresh_from_db()
    assert response.json() == {
        "id": subaccount.pk,
        "identifier": "New identifier",
        "description": "New Description",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": 10.0,
        "rate": 1.5,
        "multiplier": subaccount.multiplier,
        "type": "subaccount",
        "object_id": account.pk,
        "parent_type": "account",
        "nominal_value": 15.0,
        "fringe_contribution": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "fringes": [],
        "siblings": [],
        "created_by": user.pk,
        "updated_by": user.pk,
        "unit": None,
        "contact": None,
        "attachments": [],
        "ancestors": [
            {
                "type": "budget",
                "id": budget.pk,
                "name": budget.name,
                "domain": context,
            },
            {
                "id": account.id,
                "type": "account",
                "identifier": account.identifier,
                "description": account.description
            }
        ]
    }
    assert subaccount.description == "New Description"
    assert subaccount.identifier == "New identifier"
    assert subaccount.quantity == 10
    assert subaccount.rate == 1.5


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['template'])
def test_update_template_subaccount(api_client, user, create_subaccount,
        create_account, create_context_budget, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(
        parent=account,
        description="Original Description",
        identifier="Original identifier",
        context=context
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "description": "New Description",
        "identifier": "New identifier",
        "quantity": 10,
        "rate": 1.5
    })
    assert response.status_code == 200
    subaccount.refresh_from_db()
    assert response.json() == {
        "id": subaccount.pk,
        "identifier": "New identifier",
        "description": "New Description",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": 10,
        "rate": 1.5,
        "multiplier": subaccount.multiplier,
        "type": "subaccount",
        "object_id": account.pk,
        "parent_type": "account",
        "nominal_value": 15.0,
        "fringe_contribution": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "fringes": [],
        "siblings": [],
        "created_by": user.pk,
        "updated_by": user.pk,
        "unit": None,
        "ancestors": [
            {
                "type": "budget",
                "id": budget.pk,
                "name": budget.name,
                "domain": context,
            },
            {
                "id": account.id,
                "type": "account",
                "identifier": account.identifier,
                "description": account.description
            }
        ]
    }
    assert subaccount.description == "New Description"
    assert subaccount.identifier == "New identifier"
    assert subaccount.quantity == 10
    assert subaccount.rate == 1.5


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_subaccount_fringes(api_client, user, create_context_budget,
        create_account, create_fringe, create_subaccount, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    fringes = [create_fringe(budget=budget), create_fringe(budget=budget)]
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "fringes": [fringe.pk for fringe in fringes]
    })
    assert response.status_code == 200
    assert response.json()['fringes'] == [fringe.pk for fringe in fringes]
    subaccount.refresh_from_db()
    assert subaccount.fringes.count() == 2


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget'])
def test_get_subaccount_subaccounts(api_client, user, create_context_budget,
        create_subaccount, create_account, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    parent = create_subaccount(parent=account, context=context)
    another_parent = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(parent=parent, identifier='A', context=context),
        create_subaccount(parent=parent, identifier='B', context=context),
        create_subaccount(
            parent=another_parent,
            identifier='C',
            context=context
        )
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % parent.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": subaccounts[0].pk,
            "identifier": "%s" % subaccounts[0].identifier,
            "description": subaccounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[0].quantity,
            "rate": subaccounts[0].rate,
            "multiplier": subaccounts[0].multiplier,
            "type": "subaccount",
            "object_id": parent.pk,
            "parent_type": "subaccount",
            "nominal_value": 0.0,
            "fringe_contribution": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "fringes": [],
            "created_by": user.pk,
            "updated_by": user.pk,
            "contact": None,
            "unit": None,
            "attachments": [],
        },
        {
            "id": subaccounts[1].pk,
            "identifier": "%s" % subaccounts[1].identifier,
            "description": subaccounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[1].quantity,
            "rate": subaccounts[1].rate,
            "multiplier": subaccounts[1].multiplier,
            "type": "subaccount",
            "object_id": parent.pk,
            "parent_type": "subaccount",
            "nominal_value": 0.0,
            "fringe_contribution": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "fringes": [],
            "created_by": user.pk,
            "updated_by": user.pk,
            "contact": None,
            "unit": None,
            "attachments": [],
        },
    ]


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['template'])
def test_get_template_subaccount_subaccounts(api_client, user, create_account,
        create_context_budget, create_subaccount, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    parent = create_subaccount(parent=account, context=context)
    another_parent = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(parent=parent, identifier='A', context=context),
        create_subaccount(parent=parent, identifier='B', context=context),
        create_subaccount(
            parent=another_parent,
            identifier='C',
            context=context
        )
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % parent.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": subaccounts[0].pk,
            "identifier": "%s" % subaccounts[0].identifier,
            "description": subaccounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[0].quantity,
            "rate": subaccounts[0].rate,
            "multiplier": subaccounts[0].multiplier,
            "type": "subaccount",
            "object_id": parent.pk,
            "parent_type": "subaccount",
            "nominal_value": 0.0,
            "fringe_contribution": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "fringes": [],
            "created_by": user.pk,
            "updated_by": user.pk,
            "unit": None
        },
        {
            "id": subaccounts[1].pk,
            "identifier": "%s" % subaccounts[1].identifier,
            "description": subaccounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[1].quantity,
            "rate": subaccounts[1].rate,
            "multiplier": subaccounts[1].multiplier,
            "type": "subaccount",
            "object_id": parent.pk,
            "parent_type": "subaccount",
            "nominal_value": 0.0,
            "fringe_contribution": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "fringes": [],
            "created_by": user.pk,
            "updated_by": user.pk,
            "unit": None,
        },
    ]


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_remove_subaccount_from_group(api_client, user, create_context_budget,
        create_subaccount, create_account, models, create_group, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    group = create_group(parent=account)
    subaccount = create_subaccount(
        parent=account,
        group=group,
        context=context
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

    assert models.Group.objects.first() is None


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget'])
def test_bulk_update_subaccount_subaccounts(api_client, user, freezer, context,
        create_context_budget, create_account, create_subaccount):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(
            parent=subaccount,
            created_at=datetime.datetime(2020, 1, 1),
            context=context,
        ),
        create_subaccount(
            parent=subaccount,
            created_at=datetime.datetime(2020, 1, 2),
            context=context,
        )
    ]
    api_client.force_login(user)
    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-update-subaccounts/" % subaccount.pk,
        format='json',
        data={'data': [
            {
                'id': subaccounts[0].pk,
                'multiplier': 2,
                'quantity': 2,
                'rate': 5
            },
            {
                'id': subaccounts[1].pk,
                'multiplier': 2,
                'quantity': 2,
                'rate': 5
            }
        ]})
    assert response.status_code == 200

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the SubAccount.
    assert response.json()['data']['id'] == subaccount.pk
    assert response.json()['data']['nominal_value'] == 40.0
    assert response.json()['data']['actual'] == 0.0
    assert len(response.json()['data']['children']) == 2
    assert response.json()['data']['children'][0] == subaccounts[0].pk
    assert response.json()['data']['children'][1] == subaccounts[1].pk

    assert response.json()['budget']['id'] == budget.pk
    assert response.json()['budget']['nominal_value'] == 40.0
    assert response.json()['budget']['actual'] == 0.0

    # Make sure the SubAccount(s) are updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].multiplier == 2
    assert subaccounts[0].quantity == 2
    assert subaccounts[0].rate == 5

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].multiplier == 2
    assert subaccounts[1].quantity == 2
    assert subaccounts[1].rate == 5

    # Make sure the SubAccount is updated in the database.
    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 40.0
    assert subaccount.actual == 0.0

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 40.0
    assert account.actual == 0.0

    # Make sure the Budget is updated in the database.
    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)
    assert budget.nominal_value == 40.0
    assert budget.actual == 0.0


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_bulk_update_subaccount_subaccounts_fringes(api_client, user, context,
        create_context_budget, create_account, create_subaccount,
        create_fringe):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(
            parent=subaccount,
            created_at=datetime.datetime(2020, 1, 1),
            quantity=1,
            rate=100,
            multiplier=1,
            context=context
        ),
        create_subaccount(
            parent=subaccount,
            created_at=datetime.datetime(2020, 1, 2),
            quantity=1,
            rate=100,
            multiplier=1,
            context=context
        )
    ]
    fringes = [
        create_fringe(budget=budget, rate=0.5),
        create_fringe(budget=budget, rate=0.2)
    ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-update-subaccounts/" % subaccount.pk,
        format='json',
        data={
            'data': [
                {
                    'id': subaccounts[0].pk,
                    'fringes': [f.pk for f in fringes]
                },
                {
                    'id': subaccounts[1].pk,
                    'description': 'New Desc',
                }
            ]
        })

    assert response.status_code == 200

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the SubAccount.
    assert response.json()['data']['id'] == subaccount.pk
    assert response.json()['data']['nominal_value'] == 200.0
    assert response.json()['data']['accumulated_fringe_contribution'] == 70.0
    assert response.json()['data']['actual'] == 0.0
    assert len(response.json()['data']['children']) == 2
    assert response.json()['data']['children'][0] == subaccounts[0].pk
    assert response.json()['data']['children'][1] == subaccounts[1].pk

    assert response.json()['budget']['id'] == budget.pk
    assert response.json()['budget']['nominal_value'] == 200.0
    assert response.json()['budget']['accumulated_fringe_contribution'] == 70.0
    assert response.json()['budget']['actual'] == 0.0

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 200.0
    assert account.accumulated_fringe_contribution == 70.0
    assert account.actual == 0.0

    # Make sure the SubAccount is updated in the database.
    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 200.0
    assert subaccount.accumulated_fringe_contribution == 70.0
    assert subaccount.actual == 0.0

    # Make sure the SubAccount(s) are updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100
    assert subaccounts[0].fringe_contribution == 70.0
    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 100
    assert subaccounts[1].fringe_contribution == 0.0

    # Make sure the Budget is updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 200.0
    assert budget.accumulated_fringe_contribution == 70.0


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_bulk_delete_subaccount_subaccounts(api_client, user, create_account,
        create_context_budget, create_subaccount, models, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(
            parent=subaccount,
            quantity=1,
            rate=100,
            multiplier=1,
            context=context
        ),
        create_subaccount(
            parent=subaccount,
            quantity=1,
            rate=100,
            multiplier=1,
            context=context
        )
    ]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-delete-subaccounts/" % subaccount.pk,
        data={'ids': [sub.pk for sub in subaccounts]}
    )
    assert response.status_code == 200
    assert models.SubAccount.objects.count() == 1

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the SubAccount.
    assert response.json()['data']['id'] == subaccount.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert response.json()['data']['actual'] == 0.0
    assert len(response.json()['data']['children']) == 0

    assert response.json()['budget']['id'] == budget.pk
    assert response.json()['budget']['nominal_value'] == 0.0
    assert response.json()['budget']['actual'] == 0.0

    # Make sure the SubAccount is updated in the database.
    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 0.0
    assert subaccount.actual == 0.0

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 0.0
    assert account.actual == 0.0

    # Make sure the Budget is updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 0.0


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_bulk_update_subaccount_subaccounts_budget_updated_once(api_client,
        user, create_context_budget, create_account, context, create_subaccount):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(parent=subaccount, context=context),
        create_subaccount(parent=subaccount, context=context)
    ]
    api_client.force_login(user)
    with mock.patch(
            'greenbudget.app.budget.models.BaseBudget.mark_updated') as save:
        response = api_client.patch(
            "/v1/subaccounts/%s/bulk-update-subaccounts/" % subaccount.pk,
            format='json',
            data={
                'data': [
                    {
                        'id': subaccounts[0].pk,
                        'description': 'New Desc 1',
                    },
                    {
                        'id': subaccounts[1].pk,
                        'description': 'New Desc 2',
                    }
                ]
            })
    assert response.status_code == 200
    assert save.call_count == 1


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_bulk_create_subaccount_subaccounts(api_client, user, create_account,
        create_context_budget, create_subaccount, models, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-create-subaccounts/" % subaccount.pk,
        format='json',
        data={'data': [
            {
                'multiplier': 2,
                'quantity': 2,
                'rate': 5
            },
            {
                'multiplier': 2,
                'quantity': 2,
                'rate': 5
            }
        ]})
    assert response.status_code == 201

    subaccounts = models.SubAccount.objects.exclude(pk=subaccount.pk)
    assert len(subaccounts) == 2

    assert len(response.json()['children']) == 2
    assert response.json()['children'][0]['id'] == subaccounts[0].pk
    assert response.json()['children'][0]['nominal_value'] == 20.0
    assert response.json()['children'][0]['actual'] == 0.0
    assert response.json()['children'][1]['id'] == subaccounts[1].pk
    assert response.json()['children'][1]['nominal_value'] == 20.0
    assert response.json()['children'][1]['actual'] == 0.0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the SubAccount.
    assert response.json()['data']['id'] == subaccount.pk
    assert response.json()['data']['nominal_value'] == 40.0
    assert response.json()['data']['actual'] == 0.0
    assert len(response.json()['data']['children']) == 2
    assert response.json()['data']['children'][0] == subaccounts[0].pk
    assert response.json()['data']['children'][1] == subaccounts[1].pk

    assert response.json()['budget']['id'] == budget.pk
    assert response.json()['budget']['nominal_value'] == 40.0
    assert response.json()['budget']['actual'] == 0.0

    # Make sure the SubAccount(s) are updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].multiplier == 2
    assert subaccounts[0].quantity == 2
    assert subaccounts[0].rate == 5

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].multiplier == 2
    assert subaccounts[1].quantity == 2
    assert subaccounts[1].rate == 5

    # Make sure the SubAccount is updated in the database.
    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 40.0
    assert subaccount.actual == 0.0

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 40.0
    assert account.actual == 0.0

    # Make sure the Budget is updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 40.0
    assert budget.actual == 0.0
