import datetime
import pytest


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
        "budget": account.budget.pk,
        "type": "account",
        "estimated": None,
        "variance": None,
        "actual": None,
        "subaccounts": [],
        "group": None,
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
        "budget": account.budget.pk,
        "type": "account",
        "estimated": None,
        "subaccounts": [],
        "group": None,
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
        "budget": budget.pk,
        "type": "account",
        "estimated": None,
        "variance": None,
        "actual": None,
        "subaccounts": [],
        "group": None,
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
        "budget": template.pk,
        "type": "account",
        "estimated": None,
        "subaccounts": [],
        "group": None,
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
        create_budget_account, create_budget_subaccount):
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
    response = api_client.patch(
        "/v1/accounts/%s/bulk-update-subaccounts/" % account.pk,
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
    assert response.json()['subaccounts'][0] == subaccounts[0].pk
    assert response.json()['subaccounts'][1] == subaccounts[1].pk

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].name == "New Name 1"
    subaccounts[1].refresh_from_db()
    assert subaccounts[1].name == "New Name 2"


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_template_account_subaccounts(api_client, user,
        create_template, create_template_account, create_template_subaccount):
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
        "/v1/accounts/%s/bulk-update-subaccounts/" % account.pk,
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
    assert response.json()['subaccounts'][0] == subaccounts[0].pk
    assert response.json()['subaccounts'][1] == subaccounts[1].pk

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].name == "New Name 1"
    subaccounts[1].refresh_from_db()
    assert subaccounts[1].name == "New Name 2"


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
                    'name': 'New Name 1',
                },
                {
                    'identifier': 'subaccount-b',
                    'name': 'New Name 2',
                }
            ]
        })
    assert response.status_code == 201

    subaccounts = models.BudgetSubAccount.objects.all()
    assert len(subaccounts) == 2
    assert subaccounts[0].identifier == "subaccount-a"
    assert subaccounts[0].name == "New Name 1"
    assert subaccounts[0].budget == budget
    assert subaccounts[0].parent == account
    assert subaccounts[1].name == "New Name 2"
    assert subaccounts[1].identifier == "subaccount-b"
    assert subaccounts[1].budget == budget
    assert subaccounts[1].parent == account

    assert response.json()['data'][0]['identifier'] == 'subaccount-a'
    assert response.json()['data'][0]['name'] == 'New Name 1'
    assert response.json()['data'][1]['identifier'] == 'subaccount-b'
    assert response.json()['data'][1]['name'] == 'New Name 2'


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_budget_account_subaccounts_count(api_client, user,
        create_budget, create_budget_account, models):
    api_client.force_login(user)
    budget = create_budget()
    account = create_budget_account(budget=budget)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-subaccounts/" % account.pk,
        format='json',
        data={'count': 2}
    )
    assert response.status_code == 201

    subaccounts = models.BudgetSubAccount.objects.all()
    assert len(subaccounts) == 2
    assert len(response.json()['data']) == 2


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_template_account_subaccounts(api_client, user,
        create_template, create_template_account, models):
    api_client.force_login(user)
    template = create_template()
    account = create_template_account(budget=template)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-subaccounts/" % account.pk,
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

    subaccounts = models.TemplateSubAccount.objects.all()
    assert len(subaccounts) == 2
    assert subaccounts[0].identifier == "subaccount-a"
    assert subaccounts[0].name == "New Name 1"
    assert subaccounts[0].budget == template
    assert subaccounts[0].parent == account
    assert subaccounts[1].name == "New Name 2"
    assert subaccounts[1].identifier == "subaccount-b"
    assert subaccounts[1].budget == template
    assert subaccounts[1].parent == account

    assert response.json()['data'][0]['identifier'] == 'subaccount-a'
    assert response.json()['data'][0]['name'] == 'New Name 1'
    assert response.json()['data'][1]['identifier'] == 'subaccount-b'
    assert response.json()['data'][1]['name'] == 'New Name 2'


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_template_account_subaccounts_count(api_client, user,
        create_template, create_template_account, models):
    api_client.force_login(user)
    template = create_template()
    account = create_template_account(budget=template)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-subaccounts/" % account.pk,
        format='json',
        data={'count': 2}
    )
    assert response.status_code == 201

    subaccounts = models.TemplateSubAccount.objects.all()
    assert len(subaccounts) == 2
    assert len(response.json()['data']) == 2
