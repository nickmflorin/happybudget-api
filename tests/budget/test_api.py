import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_budgets(api_client, user, admin_user, create_budget):
    budgets = create_budget(count=2)
    # Add additional budgets created by another use to ensure that those are
    # not included in the response.
    create_budget(count=2, created_by=admin_user)
    # Add additional archived budgets to ensure that those are not included in
    # the response.
    create_budget(count=2, created_by=user, archived=True)
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": budgets[0].pk,
            "name": budgets[0].name,
            "type": "budget",
            "domain": "budget",
            "image": None,
            "updated_at": "2020-01-01 00:00:00",
            "is_permissioned": False
        },
        {
            "id": budgets[1].pk,
            "name": budgets[1].name,
            "type": "budget",
            "domain": "budget",
            "image": None,
            "updated_at": "2020-01-01 00:00:00",
            "is_permissioned": True
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_archived_budgets(api_client, user, admin_user, create_budget):
    archived_budgets = create_budget(count=2, archived=True)
    # Add additional budgets created by another use to ensure that those are
    # not included in the response.
    create_budget(count=2, created_by=admin_user, archived=True)
    # Add additional non-archived budgets to ensure that those are not included
    # in the response.
    create_budget(count=2, created_by=user)
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/archived/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": archived_budgets[0].pk,
            "name": archived_budgets[0].name,
            "type": "budget",
            "domain": "budget",
            "image": None,
            "updated_at": "2020-01-01 00:00:00",
            "is_permissioned": False
        },
        {
            "id": archived_budgets[1].pk,
            "name": archived_budgets[1].name,
            "type": "budget",
            "domain": "budget",
            "image": None,
            "updated_at": "2020-01-01 00:00:00",
            "is_permissioned": True
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_collaborating_budgets(api_client, create_budget, create_user,
        create_collaborator):
    users = create_user(count=4)
    budgets = create_budget(count=4, created_by_array=users)
    # The second budget cannot have a collaborator assigned as the second user
    # because the second user will be registered as the creator of the second
    # budget.
    _ = [
        create_collaborator(instance=budgets[0], user=users[1]),
        create_collaborator(instance=budgets[2], user=users[1]),
        create_collaborator(instance=budgets[3], user=users[1]),
    ]
    api_client.force_login(users[1])
    response = api_client.get("/v1/budgets/collaborating/")
    assert response.status_code == 200
    assert response.json()['count'] == 3
    assert response.json()['data'] == [
        {
            "id": budgets[0].pk,
            "name": budgets[0].name,
            "type": "budget",
            "domain": "budget",
            "image": None,
            "updated_at": "2020-01-01 00:00:00"
        },
        {
            "id": budgets[2].pk,
            "name": budgets[2].name,
            "type": "budget",
            "domain": "budget",
            "image": None,
            "updated_at": "2020-01-01 00:00:00"
        },
        {
            "id": budgets[3].pk,
            "name": budgets[3].name,
            "type": "budget",
            "domain": "budget",
            "image": None,
            "updated_at": "2020-01-01 00:00:00"
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget(api_client, user, create_budget):
    budget = create_budget()
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "budget",
        "image": None,
        "is_permissioned": False,
        "public_token": None
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
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "budget",
        "image": None,
        "is_permissioned": False,
        "public_token": None
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget(api_client, user, models):
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/", data={"name": "Test Name"})
    assert response.status_code == 201
    budget = models.Budget.objects.first()
    assert budget is not None
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "budget",
        "image": None,
        "is_permissioned": False,
        "public_token": None
    }


@pytest.mark.freeze_time('2020-01-01')
def test_derive_budget(api_client, user, template_df, staff_user, models):
    template = template_df.create_budget(created_by=staff_user)
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
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "budget",
        "image": None,
        "is_permissioned": False,
        "public_token": None
    }


@pytest.mark.freeze_time('2020-01-01')
def test_duplicate_budget(api_client, standard_product_user, create_budget,
        models):
    original = create_budget(created_by=standard_product_user)
    api_client.force_login(standard_product_user)
    response = api_client.post("/v1/budgets/%s/duplicate/" % original.pk)
    assert response.status_code == 201
    assert models.Budget.objects.count() == 2
    budget = models.Budget.objects.all()[1]
    assert response.json() == {
        "id": budget.pk,
        "name": original.name,
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "budget",
        "image": None,
        "is_permissioned": False,
        "public_token": None
    }


def test_duplicate_archived_budget(api_client, standard_product_user,
        create_budget):
    original = create_budget(created_by=standard_product_user, archived=True)
    api_client.force_login(standard_product_user)
    response = api_client.post("/v1/budgets/%s/duplicate/" % original.pk)
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'Duplicating archived budgets is not permitted.',
        'code': 'bad_request',
        'error_type': 'bad_request'
    }]}


def test_delete_budget(api_client, user, create_budget, models,
        create_budget_account, create_budget_subaccount):
    budget = create_budget()
    accounts = [
        create_budget_account(parent=budget),
        create_budget_account(parent=budget),
        create_budget_account(parent=budget)
    ]
    create_budget_subaccount(count=6, parent=accounts[0])
    create_budget_subaccount(count=6, parent=accounts[1])
    create_budget_subaccount(count=6, parent=accounts[2])

    api_client.force_login(user)
    response = api_client.delete("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 204
    assert models.Budget.objects.count() == 0
    assert models.Account.objects.count() == 0
    assert models.SubAccount.objects.count() == 0


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_pdf(api_client, user, create_budget, create_markup,
        create_budget_account, create_budget_subaccount):
    budget = create_budget()
    budget_markups = [create_markup(parent=budget)]
    account = create_budget_account(parent=budget, markups=budget_markups)
    account_markups = [create_markup(parent=account)]
    subaccount = create_budget_subaccount(
        parent=account,
        markups=account_markups
    )
    subaccounts = [
        create_budget_subaccount(parent=subaccount),
        create_budget_subaccount(parent=subaccount)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/pdf/" % budget.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "groups": [],
        "nominal_value": 0.0,
        "type": "pdf-budget",
        "domain": "budget",
        "accumulated_markup_contribution": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "actual": 0.0,
        "children_markups": [{
            "id": budget_markups[0].pk,
            "type": "markup",
            "identifier": budget_markups[0].identifier,
            "description": budget_markups[0].description,
            "rate": budget_markups[0].rate,
            "actual": 0.0,
            "unit": {
                "id": budget_markups[0].unit,
                "name": budget_markups[0].UNITS[budget_markups[0].unit]
            },
            "children": [account.pk]
        }],
        "children": [
            {
                "id": account.pk,
                "identifier": account.identifier,
                "type": "pdf-account",
                "domain": "budget",
                "description": account.description,
                "nominal_value": 0.0,
                "markup_contribution": 0.0,
                "accumulated_markup_contribution": 0.0,
                "accumulated_fringe_contribution": 0.0,
                "actual": 0.0,
                "groups": [],
                "order": "n",
                "children_markups": [{
                    "id": account_markups[0].pk,
                    "type": "markup",
                    "identifier": account_markups[0].identifier,
                    "description": account_markups[0].description,
                    "rate": account_markups[0].rate,
                    "actual": 0.0,
                    "unit": {
                        "id": account_markups[0].unit,
                        "name": account_markups[0].UNITS[account_markups[0].unit]
                    },
                    "children": [subaccount.pk]
                }],
                "children": [
                    {
                        "id": subaccount.pk,
                        "identifier": subaccount.identifier,
                        "type": "pdf-subaccount",
                        "domain": "budget",
                        "description": subaccount.description,
                        "nominal_value": 0.0,
                        "fringe_contribution": 0.0,
                        "markup_contribution": 0.0,
                        "accumulated_markup_contribution": 0.0,
                        "accumulated_fringe_contribution": 0.0,
                        "actual": 0.0,
                        "quantity": None,
                        "rate": None,
                        "multiplier": None,
                        "unit": None,
                        "contact": None,
                        "group": None,
                        "groups": [],
                        "children_markups": [],
                        "order": "n",
                        "children": [
                            {
                                "id": subaccounts[0].pk,
                                "identifier": subaccounts[0].identifier,
                                "type": "pdf-subaccount",
                                "domain": "budget",
                                "description": subaccounts[0].description,
                                "nominal_value": 0.0,
                                "fringe_contribution": 0.0,
                                "markup_contribution": 0.0,
                                "accumulated_markup_contribution": 0.0,
                                "accumulated_fringe_contribution": 0.0,
                                "actual": 0.0,
                                "quantity": None,
                                "rate": None,
                                "multiplier": None,
                                "unit": None,
                                "children": [],
                                "children_markups": [],
                                "contact": None,
                                "group": None,
                                "groups": [],
                                "order": "n",
                            },
                            {
                                "id": subaccounts[1].pk,
                                "identifier": subaccounts[1].identifier,
                                "type": "pdf-subaccount",
                                "domain": "budget",
                                "description": subaccounts[1].description,
                                "nominal_value": 0.0,
                                "fringe_contribution": 0.0,
                                "markup_contribution": 0.0,
                                "accumulated_markup_contribution": 0.0,
                                "accumulated_fringe_contribution": 0.0,
                                "actual": 0.0,
                                "quantity": None,
                                "rate": None,
                                "multiplier": None,
                                "unit": None,
                                "children": [],
                                "children_markups": [],
                                "contact": None,
                                "group": None,
                                "groups": [],
                                "order": "t",
                            }
                        ]
                    }
                ],
            }
        ],
    }
