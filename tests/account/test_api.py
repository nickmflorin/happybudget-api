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
    account = create_budget_account(budget=budget)
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
        "estimated": 0.0,
        "variance": 0.0,
        "actual": 0.0,
        "subaccounts": [],
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
    account = create_template_account(budget=template)
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
        "estimated": 0.0,
        "subaccounts": [],
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
        budget=budget,
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
        "estimated": 0.0,
        "variance": 0.0,
        "actual": 0.0,
        "subaccounts": [],
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
        budget=template,
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
        "estimated": 0.0,
        "subaccounts": [],
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
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccounts = [
        create_budget_subaccount(
            budget=budget,
            parent=account,
            created_at=datetime.datetime(2020, 1, 1)
        ),
        create_budget_subaccount(
            budget=budget,
            parent=account,
            created_at=datetime.datetime(2020, 1, 2)
        )
    ]
    api_client.force_login(user)
    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/accounts/%s/bulk-update-subaccounts/" % account.pk,
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
    assert response.json()['subaccounts'][0] == subaccounts[0].pk
    assert response.json()['subaccounts'][1] == subaccounts[1].pk

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].description == "New Desc 1"
    subaccounts[1].refresh_from_db()
    assert subaccounts[1].description == "New Desc 2"

    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)


def test_bulk_update_budget_account_subaccounts_fringes(api_client, user,
        create_budget, create_budget_account, create_budget_subaccount,
        create_fringe):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccounts = [
        create_budget_subaccount(
            budget=budget,
            parent=account,
            created_at=datetime.datetime(2020, 1, 1),
            quantity=1,
            rate=100,
            multiplier=1
        ),
        create_budget_subaccount(
            budget=budget,
            parent=account,
            created_at=datetime.datetime(2020, 1, 2),
            estimated=100,
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
                    'description': 'New Desc 1',
                    'fringes': [f.pk for f in fringes]
                },
                {
                    'id': subaccounts[1].pk,
                    'description': 'New Desc 2',
                }
            ]
        })
    assert response.status_code == 200
    assert response.json()['subaccounts'][0] == subaccounts[0].pk
    assert response.json()['subaccounts'][1] == subaccounts[1].pk

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].description == "New Desc 1"
    assert subaccounts[0].estimated == 170
    subaccounts[1].refresh_from_db()
    assert subaccounts[1].description == "New Desc 2"
    assert subaccounts[1].estimated == 100

    budget.refresh_from_db()
    assert budget.estimated == 270


def test_bulk_delete_budget_account_subaccounts(api_client, user,
        create_budget, create_budget_account, create_budget_subaccount,
        models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccounts = [
        create_budget_subaccount(budget=budget, parent=account),
        create_budget_subaccount(budget=budget, parent=account)
    ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-delete-subaccounts/" % account.pk,
        data={'ids': [sub.pk for sub in subaccounts]}
    )
    assert response.status_code == 200
    assert models.BudgetSubAccount.objects.count() == 0


def test_bulk_update_budget_account_subaccounts_budget_updated_once(api_client,
        user, create_budget, create_budget_account, create_budget_subaccount):

    with signals.post_save.disable():
        budget = create_budget()
        account = create_budget_account(budget=budget)
        subaccounts = [
            create_budget_subaccount(
                budget=budget,
                parent=account,
                created_at=datetime.datetime(2020, 1, 1)
            ),
            create_budget_subaccount(
                budget=budget,
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
    template = create_template()
    account = create_template_account(budget=template)
    subaccounts = [
        create_template_subaccount(budget=template, parent=account),
        create_template_subaccount(budget=template, parent=account)
    ]
    api_client.force_login(user)
    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/accounts/%s/bulk-update-subaccounts/" % account.pk,
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
    assert response.json()['subaccounts'][0] == subaccounts[0].pk
    assert response.json()['subaccounts'][1] == subaccounts[1].pk

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].description == "New Desc 1"
    subaccounts[1].refresh_from_db()
    assert subaccounts[1].description == "New Desc 2"

    template.refresh_from_db()
    assert template.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)


def test_bulk_delete_template_account_subaccounts(api_client, user,
        create_template, create_template_account, create_template_subaccount,
        models):
    template = create_template()
    account = create_template_account(budget=template)
    subaccounts = [
        create_template_subaccount(
            budget=template,
            parent=account,
            created_at=datetime.datetime(2020, 1, 1)
        ),
        create_template_subaccount(
            budget=template,
            parent=account,
            created_at=datetime.datetime(2020, 1, 2)
        )
    ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-delete-subaccounts/" % account.pk,
        data={'ids': [sub.pk for sub in subaccounts]}
    )
    assert response.status_code == 200
    assert models.TemplateSubAccount.objects.count() == 0


def test_bulk_update_template_account_subaccounts_template_updated_once(
        api_client, user, create_template, create_template_account,
        create_template_subaccount):
    template = create_template()
    account = create_template_account(budget=template)
    subaccounts = [
        create_template_subaccount(
            budget=template,
            parent=account,
            created_at=datetime.datetime(2020, 1, 1)
        ),
        create_template_subaccount(
            budget=template,
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
    api_client.force_login(user)
    budget = create_budget()
    account = create_budget_account(budget=budget)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-subaccounts/" % account.pk,
        format='json',
        data={
            'data': [
                {
                    'identifier': 'subaccount-a',
                    'description': 'New Desc 1',
                },
                {
                    'identifier': 'subaccount-b',
                    'description': 'New Desc 2',
                }
            ]
        })
    assert response.status_code == 201

    subaccounts = models.BudgetSubAccount.objects.all()
    assert len(subaccounts) == 2
    assert subaccounts[0].identifier == "subaccount-a"
    assert subaccounts[0].description == "New Desc 1"
    assert subaccounts[0].budget == budget
    assert subaccounts[0].parent == account
    assert subaccounts[1].description == "New Desc 2"
    assert subaccounts[1].identifier == "subaccount-b"
    assert subaccounts[1].budget == budget
    assert subaccounts[1].parent == account

    assert response.json()['data'][0]['identifier'] == 'subaccount-a'
    assert response.json()['data'][0]['description'] == 'New Desc 1'
    assert response.json()['data'][1]['identifier'] == 'subaccount-b'
    assert response.json()['data'][1]['description'] == 'New Desc 2'


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_budget_account_subaccounts_count(api_client, user,
        create_budget, create_budget_account, models, freezer):
    api_client.force_login(user)
    budget = create_budget()
    account = create_budget_account(budget=budget)
    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-subaccounts/" % account.pk,
        format='json',
        data={'count': 2}
    )
    assert response.status_code == 201

    subaccounts = models.BudgetSubAccount.objects.all()
    assert len(subaccounts) == 2
    assert len(response.json()['data']) == 2
    budget.refresh_from_db()
    assert budget.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_template_account_subaccounts(api_client, user,
        create_template, create_template_account, models, freezer):
    api_client.force_login(user)
    template = create_template()
    account = create_template_account(budget=template)

    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-subaccounts/" % account.pk,
        format='json',
        data={
            'data': [
                {
                    'identifier': 'subaccount-a',
                    'description': 'New Desc 1',
                },
                {
                    'identifier': 'subaccount-b',
                    'description': 'New Desc 2',
                }
            ]
        })
    assert response.status_code == 201

    subaccounts = models.TemplateSubAccount.objects.all()
    assert len(subaccounts) == 2
    assert subaccounts[0].identifier == "subaccount-a"
    assert subaccounts[0].description == "New Desc 1"
    assert subaccounts[0].budget == template
    assert subaccounts[0].parent == account
    assert subaccounts[1].description == "New Desc 2"
    assert subaccounts[1].identifier == "subaccount-b"
    assert subaccounts[1].budget == template
    assert subaccounts[1].parent == account

    assert response.json()['data'][0]['identifier'] == 'subaccount-a'
    assert response.json()['data'][0]['description'] == 'New Desc 1'
    assert response.json()['data'][1]['identifier'] == 'subaccount-b'
    assert response.json()['data'][1]['description'] == 'New Desc 2'

    template.refresh_from_db()
    assert template.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_template_account_subaccounts_count(api_client, user,
        create_template, create_template_account, models, freezer):
    api_client.force_login(user)
    template = create_template()
    account = create_template_account(budget=template)

    freezer.move_to("2021-01-01")
    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-subaccounts/" % account.pk,
        format='json',
        data={'count': 2}
    )
    assert response.status_code == 201

    subaccounts = models.TemplateSubAccount.objects.all()
    assert len(subaccounts) == 2
    assert len(response.json()['data']) == 2

    template.refresh_from_db()
    assert template.updated_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=timezone.utc)
