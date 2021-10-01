import datetime
from datetime import timezone
import pytest
import mock

from greenbudget.app import signals


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_account(api_client, user, create_budget_account,
        create_budget):
    api_client.force_login(user)
    budget = create_budget()
    account = create_budget_account(parent=budget)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": account.pk,
        "identifier": "%s" % account.identifier,
        "description": account.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "type": "account",
        "nominal_value": 0.0,
        "accumulated_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "created_by": user.pk,
        "updated_by": user.pk,
        "siblings": [],
        "ancestors": [{
            "type": "budget",
            "id": budget.pk,
            "name": budget.name
        }]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_account(api_client, user, create_template_account,
        create_template):
    template = create_template()
    account = create_template_account(parent=template)
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": account.pk,
        "identifier": "%s" % account.identifier,
        "description": account.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "type": "account",
        "nominal_value": 0.0,
        "accumulated_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "created_by": user.pk,
        "updated_by": user.pk,
        "siblings": [],
        "ancestors": [{
            "type": "template",
            "id": template.pk,
            "name": template.name
        }],
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget_account(api_client, user, create_budget,
        create_budget_account):
    budget = create_budget()
    account = create_budget_account(
        parent=budget,
        identifier="original_identifier"
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % account.pk, data={
        'identifier': 'new_account',
        'description': 'Account description'
    })
    assert response.status_code == 200
    assert response.json() == {
        "id": account.pk,
        "identifier": 'new_account',
        "description": 'Account description',
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "type": "account",
        "nominal_value": 0.0,
        "accumulated_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "created_by": user.pk,
        "updated_by": user.pk,
        "siblings": [],
        "ancestors": [{
            "type": "budget",
            "id": budget.pk,
            "name": budget.name
        }]
    }
    account.refresh_from_db()
    assert account.identifier == "new_account"
    assert account.description == "Account description"


@pytest.mark.freeze_time('2020-01-01')
def test_update_template_account(api_client, user, create_template,
        create_template_account):
    template = create_template()
    account = create_template_account(
        parent=template,
        identifier="original_identifier"
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % account.pk, data={
        'identifier': 'new_account',
        'description': 'Account description'
    })
    assert response.status_code == 200
    assert response.json() == {
        "id": account.pk,
        "identifier": 'new_account',
        "description": 'Account description',
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "type": "account",
        "nominal_value": 0.0,
        "accumulated_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "created_by": user.pk,
        "updated_by": user.pk,
        "siblings": [],
        "ancestors": [{
            "type": "template",
            "id": template.pk,
            "name": template.name
        }]
    }
    account.refresh_from_db()
    assert account.identifier == "new_account"
    assert account.description == "Account description"


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_budget_account_subaccounts(api_client, user, create_budget,
        create_budget_account, create_budget_subaccount, freezer):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        subaccounts = [
            create_budget_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 1)
            ),
            create_budget_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 2)
            )
        ]
    api_client.force_login(user)
    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/accounts/%s/bulk-update-subaccounts/" % account.pk,
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
    # the Account.
    assert response.json()['data']['id'] == account.pk
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


def test_bulk_update_budget_account_subaccounts_fringes(api_client, user,
        create_budget, create_budget_account, create_budget_subaccount,
        create_fringe):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        subaccounts = [
            create_budget_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 1),
                quantity=1,
                rate=100,
                multiplier=1
            ),
            create_budget_subaccount(
                parent=account,
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
        "/v1/accounts/%s/bulk-update-subaccounts/" % account.pk,
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
    # the Account.
    assert response.json()['data']['id'] == account.pk
    assert response.json()['data']['nominal_value'] == 200.0
    assert response.json()['data']['accumulated_fringe_contribution'] == 70.0
    assert response.json()['data']['actual'] == 0.0
    assert len(response.json()['data']['children']) == 2
    assert response.json()['data']['children'][0] == subaccounts[0].pk
    assert response.json()['data']['children'][1] == subaccounts[1].pk

    assert response.json()['budget']['id'] == budget.pk
    assert response.json()['budget']['nominal_value'] == 200.0
    assert response.json()['budget']['accumulated_fringe_contribution'] == 70.0

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 200.0
    assert account.accumulated_fringe_contribution == 70.0
    assert account.actual == 0.0

    # Make sure the SubAccount(s) are updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100
    assert subaccounts[0].fringe_contribution == 70.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 100
    assert subaccounts[1].fringe_contribution == 0

    # Make sure the Budget is updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 200.0
    assert budget.accumulated_fringe_contribution == 70.0


def test_bulk_delete_budget_account_subaccounts(api_client, user,
        create_budget, create_budget_account, create_budget_subaccount,
        models):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)

    subaccounts = [
        create_budget_subaccount(
            parent=account,
            quantity=1,
            rate=100,
            multiplier=1
        ),
        create_budget_subaccount(
            parent=account,
            quantity=1,
            rate=100,
            multiplier=1
        )
    ]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-delete-subaccounts/" % account.pk,
        data={'ids': [sub.pk for sub in subaccounts]}
    )
    assert response.status_code == 200
    assert models.BudgetSubAccount.objects.count() == 0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Account.
    assert response.json()['data']['id'] == account.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert response.json()['data']['actual'] == 0.0
    assert len(response.json()['data']['children']) == 0

    assert response.json()['budget']['id'] == budget.pk
    assert response.json()['budget']['nominal_value'] == 0.0
    assert response.json()['budget']['actual'] == 0.0

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 0.0
    assert account.actual == 0.0

    # Make sure the Budget is updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 0.0


def test_bulk_update_budget_account_subaccounts_budget_updated_once(api_client,
        user, create_budget, create_budget_account, create_budget_subaccount):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)
        subaccounts = [
            create_budget_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 1)
            ),
            create_budget_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 2)
            )
        ]
    api_client.force_login(user)
    with mock.patch('greenbudget.app.budget.signals.Budget.save') as save:
        response = api_client.patch(
            "/v1/accounts/%s/bulk-update-subaccounts/" % account.pk,
            format='json',
            data={
                'data': [
                    {
                        'id': subaccounts[0].pk,
                        'name': 'New Desc 1',
                    },
                    {
                        'id': subaccounts[1].pk,
                        'name': 'New Desc 2',
                    }
                ]
            })
    assert response.status_code == 200
    assert save.call_count == 1


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_template_account_subaccounts(api_client, user,
        create_template, create_template_account, create_template_subaccount,
        freezer):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)
        subaccounts = [
            create_template_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 1)
            ),
            create_template_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 2)
            )
        ]

    api_client.force_login(user)
    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/accounts/%s/bulk-update-subaccounts/" % account.pk,
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
    # the Account.
    assert response.json()['data']['id'] == account.pk
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

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 40.0

    # Make sure the Template is updated in the database.
    template.refresh_from_db()
    assert template.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)
    assert template.nominal_value == 40.0


def test_bulk_delete_template_account_subaccounts(api_client, user,
        create_template, create_template_account, create_template_subaccount,
        models):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)

    subaccounts = [
        create_template_subaccount(
            parent=account,
            quantity=1,
            rate=100,
            multiplier=1
        ),
        create_template_subaccount(
            parent=account,
            quantity=1,
            rate=100,
            multiplier=1
        )
    ]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-delete-subaccounts/" % account.pk,
        data={'ids': [sub.pk for sub in subaccounts]}
    )
    assert response.status_code == 200
    assert models.TemplateSubAccount.objects.count() == 0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Account.
    assert response.json()['data']['id'] == account.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert len(response.json()['data']['children']) == 0

    assert response.json()['budget']['id'] == template.pk
    assert response.json()['budget']['nominal_value'] == 0.0

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 0.0

    # Make sure the Template is updated in the database.
    template.refresh_from_db()
    assert template.nominal_value == 0.0


def test_bulk_update_template_account_subaccounts_template_updated_once(
        api_client, user, create_template, create_template_account,
        create_template_subaccount):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)
        subaccounts = [
            create_template_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 1)
            ),
            create_template_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 2)
            )
        ]
    api_client.force_login(user)
    with mock.patch(
            'greenbudget.app.template.models.Template.save') as save:
        response = api_client.patch(
            "/v1/accounts/%s/bulk-update-subaccounts/" % account.pk,
            format='json',
            data={
                'data': [
                    {
                        'id': subaccounts[0].pk,
                        'name': 'New Desc 1',
                    },
                    {
                        'id': subaccounts[1].pk,
                        'name': 'New Desc 2',
                    }
                ]
            })
    assert response.status_code == 200
    assert save.call_count == 1


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_budget_account_subaccounts(api_client, user, create_budget,
        create_budget_account, models):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(parent=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-subaccounts/" % account.pk,
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

    subaccounts = models.BudgetSubAccount.objects.all()
    assert len(subaccounts) == 2

    assert len(response.json()['children']) == 2
    assert response.json()['children'][0]['id'] == subaccounts[0].pk
    assert response.json()['children'][0]['nominal_value'] == 20.0
    assert response.json()['children'][0]['actual'] == 0.0
    assert response.json()['children'][1]['id'] == subaccounts[1].pk
    assert response.json()['children'][1]['nominal_value'] == 20.0
    assert response.json()['children'][1]['actual'] == 0.0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Account.
    assert response.json()['data']['id'] == account.pk
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
        create_template, create_template_account, models, freezer):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)

    freezer.move_to("2021-01-01")
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-subaccounts/" % account.pk,
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

    subaccounts = models.TemplateSubAccount.objects.all()
    assert len(subaccounts) == 2

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Account.
    assert response.json()['data']['id'] == account.pk
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

    # Make sure the Account is updated in the database.
    account.refresh_from_db()
    assert account.nominal_value == 40.0

    # Make sure the Template is updated in the database.
    template.refresh_from_db()
    assert template.nominal_value == 40.0
