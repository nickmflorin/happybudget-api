import datetime
from datetime import timezone
import mock
import pytest

from greenbudget.app import signals


@pytest.mark.freeze_time('2020-01-01')
def test_unit_properly_serializes(api_client, user, create_budget_subaccount,
        create_budget_account, create_budget, create_subaccount_unit):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        unit = create_subaccount_unit()
        subaccount = create_budget_subaccount(
            parent=account,
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
        'plural_title': unit.plural_title,
        'order': unit.order,
        'color': unit.color.code
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_subaccount_unit(api_client, user, create_budget_subaccount,
        create_budget_account, create_budget, create_subaccount_unit):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        subaccount = create_budget_subaccount(parent=account)
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


def test_update_subaccount_contact(api_client, user, create_budget_subaccount,
        create_budget_account, create_budget, create_contact):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        contact = create_contact(user=user)
        subaccount = create_budget_subaccount(parent=account)
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "contact": contact.pk
    })
    assert response.status_code == 200
    subaccount.refresh_from_db()
    assert response.json()['contact'] == contact.pk
    assert subaccount.contact == contact


def test_update_subaccount_contact_wrong_user(api_client, user,
        create_budget_subaccount, create_budget_account, create_budget,
        create_contact, admin_user):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        contact = create_contact(user=admin_user)
        subaccount = create_budget_subaccount(parent=account)
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "contact": contact.pk
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_subaccount(api_client, user, create_budget_subaccount,
        create_budget_account, create_budget):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        subaccount = create_budget_subaccount(parent=account)

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
        "accumulated_value": 0.0,
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
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)
        subaccount = create_template_subaccount(parent=account)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": subaccount.pk,
        "identifier": subaccount.identifier,
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
        "accumulated_value": 0.0,
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
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        subaccount = create_budget_subaccount(
            parent=account,
            description="Original Description",
            identifier="Original identifier"
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
        "accumulated_value": 0.0,
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
    assert subaccount.description == "New Description"
    assert subaccount.identifier == "New identifier"
    assert subaccount.quantity == 10
    assert subaccount.rate == 1.5


@pytest.mark.freeze_time('2020-01-01')
def test_update_subaccount_fringes(api_client, user, create_budget_subaccount,
        create_budget_account, create_budget, create_fringe):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)
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
def test_update_template_subaccount(api_client, user, create_template_account,
        create_template_subaccount, create_template):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)
        subaccount = create_template_subaccount(
            parent=account,
            description="Original Description",
            identifier="Original identifier",
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
        "accumulated_value": 0.0,
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
        "siblings": [],
        "contact": None,
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
    assert subaccount.description == "New Description"
    assert subaccount.identifier == "New identifier"
    assert subaccount.quantity == 10
    assert subaccount.rate == 1.5


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_subaccount_subaccounts(api_client, user, create_budget,
        create_budget_subaccount, create_budget_account):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        parent = create_budget_subaccount(parent=account)
        another_parent = create_budget_subaccount(parent=account)
        subaccounts = [
            create_budget_subaccount(parent=parent, identifier='A'),
            create_budget_subaccount(parent=parent, identifier='B'),
            create_budget_subaccount(
                parent=another_parent,
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
            "accumulated_value": 0.0,
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
            "accumulated_value": 0.0,
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
            "unit": None
        },
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_subaccount_subaccounts(api_client, user, create_template,
        create_template_subaccount, create_template_account):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)
        parent = create_template_subaccount(parent=account)
        another_parent = create_template_subaccount(
            parent=account)
        subaccounts = [
            create_template_subaccount(
                parent=parent,
                identifier='A'
            ),
            create_template_subaccount(
                parent=parent,
                identifier='B'
            ),
            create_template_subaccount(
                parent=another_parent,
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
            "identifier": subaccounts[0].identifier,
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
            "accumulated_value": 0.0,
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
            "accumulated_value": 0.0,
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
            "unit": None
        },
    ]


def test_remove_budget_subaccount_from_group(api_client, user, create_budget,
        create_budget_subaccount, create_budget_account, models,
        create_group):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        group = create_group(parent=account)
        subaccount = create_budget_subaccount(
            parent=account,
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

    assert models.Group.objects.first() is None


def test_remove_template_subaccount_from_group(api_client, user,
        create_template, create_template_subaccount, create_template_account,
        create_group, models):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)
        group = create_group(parent=account)
        subaccount = create_template_subaccount(
            parent=account,
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

    assert models.Group.objects.first() is None


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_subaccount_subaccounts(api_client, user,
        create_budget, create_budget_account, create_budget_subaccount,
        freezer):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        subaccount = create_budget_subaccount(parent=account)
        subaccounts = [
            create_budget_subaccount(
                parent=subaccount,
                created_at=datetime.datetime(2020, 1, 1)
            ),
            create_budget_subaccount(
                parent=subaccount,
                created_at=datetime.datetime(2020, 1, 2)
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


def test_bulk_update_budget_subaccount_subaccounts_fringes(api_client, user,
        create_budget, create_budget_account, create_budget_subaccount,
        create_fringe):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        subaccount = create_budget_subaccount(parent=account)
        subaccounts = [
            create_budget_subaccount(
                parent=subaccount,
                created_at=datetime.datetime(2020, 1, 1),
                quantity=1,
                rate=100,
                multiplier=1
            ),
            create_budget_subaccount(
                parent=subaccount,
                created_at=datetime.datetime(2020, 1, 2),
                quantity=1,
                rate=100,
                multiplier=1
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


def test_bulk_delete_budget_subaccount_subaccounts(api_client, user,
        create_budget, create_budget_account, create_budget_subaccount,
        models):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        subaccount = create_budget_subaccount(parent=account)

    # Do not do in the context of disabled signals because we need the values
    # of the different entities to be calculated.
    subaccounts = [
        create_budget_subaccount(
            parent=subaccount,
            quantity=1,
            rate=100,
            multiplier=1
        ),
        create_budget_subaccount(
            parent=subaccount,
            quantity=1,
            rate=100,
            multiplier=1
        )
    ]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-delete-subaccounts/" % subaccount.pk,
        data={'ids': [sub.pk for sub in subaccounts]}
    )
    assert response.status_code == 200
    assert models.BudgetSubAccount.objects.count() == 1

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


def test_bulk_update_budget_subaccount_subaccounts_budget_updated_once(
        api_client, user, create_budget, create_budget_account,
        create_budget_subaccount):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        subaccount = create_budget_subaccount(parent=account)
        subaccounts = [
            create_budget_subaccount(parent=subaccount),
            create_budget_subaccount(parent=subaccount)
        ]
    api_client.force_login(user)
    with mock.patch('greenbudget.app.budget.models.Budget.save') as save:
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
def test_bulk_update_template_subaccount_subaccounts(api_client, user,
        create_template, create_template_account, create_template_subaccount,
        freezer):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)
        subaccount = create_template_subaccount(parent=account)
        subaccounts = [
            create_template_subaccount(
                parent=subaccount,
                created_at=datetime.datetime(2020, 1, 1)
            ),
            create_template_subaccount(
                parent=subaccount,
                created_at=datetime.datetime(2020, 1, 2)
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
    assert len(response.json()['data']['children']) == 2
    assert response.json()['data']['children'][0] == subaccounts[0].pk
    assert response.json()['data']['children'][1] == subaccounts[1].pk

    assert response.json()['budget']['id'] == template.pk
    assert response.json()['budget']['nominal_value'] == 40.0

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

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 40.0

    # Make sure the Template is updated in the database.
    template.refresh_from_db()
    assert template.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)
    assert template.nominal_value == 40.0


def test_bulk_delete_template_subaccount_subaccounts(api_client, user,
        create_template, create_template_account, create_template_subaccount,
        models):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)
        subaccount = create_template_subaccount(parent=account)

    # Do not do in the context of disabled signals because we need the values
    # of the different entities to be calculated.
    subaccounts = [
        create_template_subaccount(
            parent=subaccount,
            quantity=1,
            rate=100,
            multiplier=1
        ),
        create_template_subaccount(
            parent=subaccount,
            quantity=1,
            rate=100,
            multiplier=1
        )
    ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-delete-subaccounts/" % subaccount.pk,
        data={'ids': [sub.pk for sub in subaccounts]}
    )
    assert response.status_code == 200
    assert models.TemplateSubAccount.objects.count() == 1

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the SubAccount.
    assert response.json()['data']['id'] == subaccount.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert len(response.json()['data']['children']) == 0

    assert response.json()['budget']['id'] == template.pk
    assert response.json()['budget']['nominal_value'] == 0.0

    # Make sure the SubAccount is updated in the database.
    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 0.0

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 0.0

    # Make sure the Template is updated in the database.
    template.refresh_from_db()
    assert template.nominal_value == 0.0


def test_bulk_update_template_subaccount_subaccounts_template_updated_once(
        api_client, user, create_template, create_template_account,
        create_template_subaccount):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)
        subaccount = create_template_subaccount(parent=account)
        subaccounts = [
            create_template_subaccount(parent=subaccount),
            create_template_subaccount(parent=subaccount)
        ]
    api_client.force_login(user)
    with mock.patch('greenbudget.app.template.models.Template.save') as save:
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
def test_bulk_create_budget_subaccount_subaccounts(api_client, user,
        create_budget, create_budget_account, create_budget_subaccount, models):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        subaccount = create_budget_subaccount(parent=account)

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

    subaccounts = models.BudgetSubAccount.objects.exclude(pk=subaccount.pk)
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


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_template_account_subaccounts(api_client, user,
        create_template, create_template_account, models, freezer,
        create_template_subaccount):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)
        subaccount = create_template_subaccount(parent=account)

    freezer.move_to("2021-01-01")
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

    subaccounts = models.TemplateSubAccount.objects.exclude(pk=subaccount.pk)
    assert len(subaccounts) == 2

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the SubAccount.
    assert response.json()['data']['id'] == subaccount.pk
    assert response.json()['data']['nominal_value'] == 40.0
    assert len(response.json()['data']['children']) == 2
    assert response.json()['data']['children'][0] == subaccounts[0].pk
    assert response.json()['data']['children'][1] == subaccounts[1].pk

    assert response.json()['budget']['id'] == template.pk
    assert response.json()['budget']['nominal_value'] == 40.0

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

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 40.0

    # Make sure the Template is updated in the database.
    template.refresh_from_db()
    assert template.nominal_value == 40.0
