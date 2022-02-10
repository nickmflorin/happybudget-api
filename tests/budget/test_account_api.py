from greenbudget.lib.utils.urls import add_query_params_to_url


def test_get_accounts(api_client, user, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(parent=budget, count=2)
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": accounts[0].pk,
            "identifier": "%s" % accounts[0].identifier,
            "description": accounts[0].description,
            "type": "account",
            "nominal_value": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "order": "n",
            "domain": budget_f.domain,
        },
        {
            "id": accounts[1].pk,
            "identifier": "%s" % accounts[1].identifier,
            "description": accounts[1].description,
            "type": "account",
            "nominal_value": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "order": "t",
            "domain": budget_f.domain,
        }
    ]


def test_get_accounts_ordered_by_group(api_client, user, budget_f, create_group):
    budget = budget_f.create_budget()
    groups = [
        create_group(parent=budget),
        create_group(parent=budget)
    ]
    [
        budget_f.create_account(parent=budget, group=groups[1], order="n"),
        budget_f.create_account(parent=budget, order="t"),
        budget_f.create_account(parent=budget, group=groups[0], order="w"),
        budget_f.create_account(parent=budget, group=groups[1], order="y"),
        budget_f.create_account(parent=budget, group=groups[0], order="yn"),
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 5
    assert [obj['id'] for obj in response.json()['data']] == [1, 4, 3, 5, 2]


def test_get_accounts_filtered_by_id(api_client, user, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(parent=budget, count=2)
    api_client.force_login(user)
    url = add_query_params_to_url(
        "/v1/budgets/%s/children/" % budget.pk,
        ids=[accounts[0].pk, 400]
    )

    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [
        {
            "id": accounts[0].pk,
            "identifier": "%s" % accounts[0].identifier,
            "description": accounts[0].description,
            "type": "account",
            "nominal_value": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "order": "n",
            "domain": budget_f.domain,
        }
    ]


def test_create_account(api_client, user, budget_f, models):
    budget = budget_f.create_budget()
    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/children/" % budget.pk,
        data={'identifier': 'new_account'}
    )
    assert response.status_code == 201

    account = models.Account.objects.first()
    assert account is not None
    assert response.json() == {
        "id": account.pk,
        "identifier": 'new_account',
        "description": None,
        "type": "account",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "table": [
            {
                "type": "account",
                "id": account.pk,
                "identifier": account.identifier,
                "description": account.description,
                "domain": budget_f.domain,
            }
        ],
        "order": "n",
        "domain": budget_f.domain,
        "ancestors": [{
            "type": "budget",
            "domain": budget_f.domain,
            "id": budget.pk,
            "name": budget.name
        }]
    }


def test_bulk_update_accounts(api_client, user, budget_f, create_group):
    budget = budget_f.create_budget()
    group = create_group(parent=budget)
    accounts = budget_f.create_account(parent=budget, count=2)
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-children/" % budget.pk,
        format='json',
        data={
            'data': [
                {
                    'id': accounts[0].pk,
                    'description': 'New Description 1',
                    'group': group.pk,
                },
                {
                    'id': accounts[1].pk,
                    'description': 'New Description 2',
                    'group': group.pk,
                }
            ]
        })
    assert response.status_code == 200

    accounts[0].refresh_from_db()
    assert accounts[0].description == "New Description 1"
    assert accounts[0].group == group

    accounts[1].refresh_from_db()
    assert accounts[1].description == "New Description 2"
    assert accounts[1].group == group

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Budget.
    assert response.json()['data']['id'] == budget.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert response.json()['data']['actual'] == 0.0


def test_bulk_update_accounts_outside_budget(api_client, user, budget_f):
    budget = budget_f.create_budget()
    another_budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=another_budget)
    ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-children/" % budget.pk,
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


def test_bulk_create_account(api_client, user, budget_f, models):
    budget = budget_f.create_budget()
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-create-children/" % budget.pk,
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

    assert len(response.json()['children']) == 2
    assert response.json()['children'][0]['id'] == accounts[0].pk
    assert response.json()['children'][0]['identifier'] == "account-a"
    assert response.json()['children'][0]['description'] == "New Description 1"
    assert response.json()['children'][1]['id'] == accounts[1].pk
    assert response.json()['children'][1]['identifier'] == "account-b"
    assert response.json()['children'][1]['description'] == "New Description 2"

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Budget.
    assert response.json()['data']['id'] == budget.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert response.json()['data']['actual'] == 0.0


def test_bulk_delete_accounts(api_client, user, budget_f, models):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(parent=budget, count=2)
    # We need to create SubAccount(s) so that the accounts themselves have
    # calculated values, and thus the Budget itself has calculated values, so
    # we can test whether or not the deletion recalculates the metrics on the
    # Budget.
    budget_f.create_subaccount(
        parent=accounts[0],
        quantity=1,
        rate=100,
        multiplier=1
    )
    budget_f.create_subaccount(
        parent=accounts[1],
        quantity=1,
        rate=100,
        multiplier=1
    )
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-delete-children/" % budget.pk,
        data={'ids': [a.pk for a in accounts]}
    )
    assert response.status_code == 200
    assert models.Account.objects.count() == 0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Budget.
    assert response.json()['data']['id'] == budget.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert response.json()['data']['actual'] == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 0.0
    assert budget.actual == 0.0
