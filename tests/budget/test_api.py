import pytest

from greenbudget.lib.utils.dateutils import api_datetime_string


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
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "created_by": user.pk,
            "type": "budget",
            "image": None,
        },
        {
            "id": budgets[1].pk,
            "name": budgets[1].name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "created_by": user.pk,
            "type": "budget",
            "image": None,
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget(api_client, user, create_budget, models):
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
            "name": models.Budget.PRODUCTION_TYPES[budget.production_type]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "shoot_date": api_datetime_string(budget.shoot_date),
        "delivery_date": api_datetime_string(budget.delivery_date),
        "build_days": budget.build_days,
        "prelight_days": budget.prelight_days,
        "studio_shoot_days": budget.studio_shoot_days,
        "location_days": budget.location_days,
        "estimated": 0.0,
        "variance": 0.0,
        "actual": 0.0,
        "created_by": user.pk,
        "type": "budget",
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget(api_client, user, create_budget, models):
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
            "name": models.Budget.PRODUCTION_TYPES[budget.production_type]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "shoot_date": api_datetime_string(budget.shoot_date),
        "delivery_date": api_datetime_string(budget.delivery_date),
        "build_days": budget.build_days,
        "prelight_days": budget.prelight_days,
        "studio_shoot_days": budget.studio_shoot_days,
        "location_days": budget.location_days,
        "estimated": 0.0,
        "variance": 0.0,
        "actual": 0.0,
        "created_by": user.pk,
        "type": "budget",
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget(api_client, user, models):
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/", data={
        "name": "Test Name",
        "production_type": 1,
    })
    assert response.status_code == 201

    budget = models.Budget.objects.first()
    assert budget is not None

    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "project_number": budget.project_number,
        "production_type": {
            "id": 1,
            "name": models.Budget.PRODUCTION_TYPES[1],
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "shoot_date": api_datetime_string(budget.shoot_date),
        "delivery_date": api_datetime_string(budget.delivery_date),
        "build_days": budget.build_days,
        "prelight_days": budget.prelight_days,
        "studio_shoot_days": budget.studio_shoot_days,
        "location_days": budget.location_days,
        "estimated": 0.0,
        "variance": 0.0,
        "actual": 0.0,
        "created_by": user.pk,
        "type": "budget",
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_derive_budget(api_client, user, create_template, staff_user, models):
    template = create_template(created_by=staff_user)

    api_client.force_login(user)
    response = api_client.post("/v1/budgets/", data={
        "name": "Test Name",
        "production_type": 1,
        "template": template.pk,
    })

    assert response.status_code == 201
    assert models.Budget.objects.count() == 1
    budget = models.Budget.objects.all()[0]
    assert response.json() == {
        "id": budget.pk,
        "name": "Test Name",
        "project_number": budget.project_number,
        "production_type": {
            "id": 1,
            "name": models.Budget.PRODUCTION_TYPES[1]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "shoot_date": api_datetime_string(budget.shoot_date),
        "delivery_date": api_datetime_string(budget.delivery_date),
        "build_days": budget.build_days,
        "prelight_days": budget.prelight_days,
        "studio_shoot_days": budget.studio_shoot_days,
        "location_days": budget.location_days,
        "estimated": 0.0,
        "variance": 0.0,
        "actual": 0.0,
        "created_by": user.pk,
        "type": "budget",
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_duplicate_budget(api_client, user, create_budget, models):
    original = create_budget(created_by=user)
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/duplicate/" % original.pk)

    assert models.Budget.objects.count() == 2
    budget = models.Budget.objects.all()[1]

    assert response.status_code == 201
    assert response.json() == {
        "id": budget.pk,
        "name": original.name,
        "project_number": original.project_number,
        "production_type": {
            "id": original.production_type,
            "name": models.Budget.PRODUCTION_TYPES[original.production_type]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "shoot_date": api_datetime_string(original.shoot_date),
        "delivery_date": api_datetime_string(original.delivery_date),
        "build_days": original.build_days,
        "prelight_days": original.prelight_days,
        "studio_shoot_days": original.studio_shoot_days,
        "location_days": original.location_days,
        "estimated": 0.0,
        "variance": 0.0,
        "actual": 0.0,
        "created_by": user.pk,
        "type": "budget",
        "image": None,
    }


def test_delete_budget(api_client, user, create_budget, models):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.delete("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 204
    assert models.Budget.objects.first() is None


def test_get_budget_subaccounts(api_client, user, create_budget,
        create_budget_account, create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    sub = create_budget_subaccount(
        budget=budget, parent=account, identifier="Jack")
    create_budget_subaccount(budget=budget, parent=account, identifier="Bob")
    api_client.force_login(user)
    response = api_client.get(
        "/v1/budgets/%s/subaccounts/?search=%s"
        % (budget.pk, "jack")
    )
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
        'id': sub.pk,
        'identifier': 'Jack',
        'description': sub.description,
        'type': 'subaccount',
    }]


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
def test_bulk_create_budget_accounts(api_client, user, create_budget, models):
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

    accounts = models.Account.objects.all()
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


def test_bulk_delete_budget_accounts(api_client, user, create_budget,
        create_budget_account, models):
    budget = create_budget()
    accounts = [
        create_budget_account(budget=budget),
        create_budget_account(budget=budget)
    ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-delete-accounts/" % budget.pk, data={
            'ids': [a.pk for a in accounts]
        })
    assert response.status_code == 200
    assert models.BudgetAccount.objects.count() == 0


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_budget_accounts_count(api_client, user, create_budget,
        models):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.patch(
        "/v1/budgets/%s/bulk-create-accounts/" % budget.pk,
        format='json',
        data={'count': 2}
    )
    assert response.status_code == 201

    accounts = models.Account.objects.all()
    assert len(accounts) == 2
    assert len(response.json()['data']) == 2
