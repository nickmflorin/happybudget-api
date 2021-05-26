def test_get_budget_items_tree(api_client, user, create_budget,
        create_budget_account, create_budget_subaccount):
    budget = create_budget()
    accounts = [
        create_budget_account(budget=budget, identifier="Account A"),
        create_budget_account(budget=budget, identifier="Account B"),
    ]
    subaccounts = [
        [
            create_budget_subaccount(
                budget=budget,
                parent=accounts[0],
                identifier="Sub Account A-A"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=accounts[0],
                identifier="Sub Account A-B"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=accounts[0],
                identifier="Sub Account A-C"
            )
        ],
        [
            create_budget_subaccount(
                budget=budget,
                parent=accounts[1],
                identifier="Sub Account B-A"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=accounts[1],
                identifier="Sub Account B-B"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=accounts[1],
                identifier="Sub Account B-C"
            )
        ]
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/items/tree/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['active_search_path'] == [
        {'id': accounts[0].pk, 'type': 'account'},
        {'id': subaccounts[0][0].pk, 'type': 'subaccount'},
        {'id': subaccounts[0][1].pk, 'type': 'subaccount'},
        {'id': subaccounts[0][2].pk, 'type': 'subaccount'},
        {'id': accounts[1].pk, 'type': 'account'},
        {'id': subaccounts[1][0].pk, 'type': 'subaccount'},
        {'id': subaccounts[1][1].pk, 'type': 'subaccount'},
        {'id': subaccounts[1][2].pk, 'type': 'subaccount'},
    ]
    assert response.json()['data'] == [
        {
            "id": accounts[0].pk,
            "identifier": "Account A",
            "type": "account",
            "description": accounts[0].description,
            "children": [
                {
                    "id": subaccounts[0][0].pk,
                    "identifier": "Sub Account A-A",
                    "type": "subaccount",
                    "name": subaccounts[0][0].name,
                    "description": subaccounts[0][0].description,
                    "children": []
                },
                {
                    "id": subaccounts[0][1].pk,
                    "identifier": "Sub Account A-B",
                    "type": "subaccount",
                    "name": subaccounts[0][1].name,
                    "description": subaccounts[0][1].description,
                    "children": []
                },
                {
                    "id": subaccounts[0][2].pk,
                    "identifier": "Sub Account A-C",
                    "type": "subaccount",
                    "name": subaccounts[0][2].name,
                    "description": subaccounts[0][2].description,
                    "children": []
                }
            ]
        },
        {
            "id": accounts[1].pk,
            "identifier": "Account B",
            "type": "account",
            "description": accounts[1].description,
            "children": [
                {
                    "id": subaccounts[1][0].pk,
                    "identifier": "Sub Account B-A",
                    "type": "subaccount",
                    "name": subaccounts[1][0].name,
                    "description": subaccounts[1][0].description,
                    "children": []
                },
                {
                    "id": subaccounts[1][1].pk,
                    "identifier": "Sub Account B-B",
                    "type": "subaccount",
                    "name": subaccounts[1][1].name,
                    "description": subaccounts[1][1].description,
                    "children": []
                },
                {
                    "id": subaccounts[1][2].pk,
                    "identifier": "Sub Account B-C",
                    "type": "subaccount",
                    "name": subaccounts[1][2].name,
                    "description": subaccounts[1][2].description,
                    "children": []
                }
            ]
        }
    ]


def test_search_budget_items_tree(api_client, user, create_budget,
        create_budget_account, create_budget_subaccount):
    budget = create_budget()
    accounts = [
        create_budget_account(budget=budget, identifier="Account A"),
        create_budget_account(budget=budget, identifier="Account B"),
        create_budget_account(budget=budget, identifier="Account Jack"),
    ]
    subaccounts_a_node = [
        create_budget_subaccount(
            budget=budget,
            parent=accounts[0],
            identifier="Sub Account A-A",
            description="Jack",
        ),
        create_budget_subaccount(
            budget=budget,
            parent=accounts[0],
            identifier="Sub Account A-B",
            description="Peter",
        ),
        create_budget_subaccount(
            budget=budget,
            parent=accounts[0],
            identifier="Sub Account A-C",
            description="Jack",
        )
    ]
    subaccounts_b_node = [
        create_budget_subaccount(
            budget=budget,
            parent=accounts[1],
            identifier="Sub Account B-A",
            description="Jack",
        ),
        create_budget_subaccount(
            budget=budget,
            parent=accounts[1],
            identifier="Sub Account B-B",
            description="Peter",
        ),
        create_budget_subaccount(
            budget=budget,
            parent=accounts[1],
            identifier="Sub Account B-C",
            description="Peter",
        )
    ]
    subaccounts_a_b_node = [
        create_budget_subaccount(
            budget=budget,
            parent=subaccounts_a_node[1],
            identifier="Sub Account A-B-A",
            description="Jack",
        )
    ]
    api_client.force_login(user)
    response = api_client.get(
        "/v1/budgets/%s/items/tree/?search=jack" % budget.pk)
    assert response.status_code == 200
    assert response.json()['active_search_path'] == [
        {'id': subaccounts_a_node[0].pk, 'type': 'subaccount'},
        {'id': subaccounts_a_b_node[0].pk, 'type': 'subaccount'},
        {'id': subaccounts_a_node[2].pk, 'type': 'subaccount'},
        {'id': subaccounts_b_node[0].pk, 'type': 'subaccount'},
        {'id': accounts[2].pk, 'type': 'account'},
    ]
    assert response.json()['data'] == [
        {
            "id": accounts[0].pk,
            "identifier": "Account A",
            "type": "account",
            "description": accounts[0].description,
            "children": [
                {
                    "id": subaccounts_a_node[0].pk,
                    "identifier": "Sub Account A-A",
                    "type": "subaccount",
                    "name": subaccounts_a_node[0].name,
                    "description": "Jack",
                    "children": []
                },
                # Included because it has a SubAccount that matches the search.
                {
                    "id": subaccounts_a_node[1].pk,
                    "identifier": "Sub Account A-B",
                    "type": "subaccount",
                    "name": subaccounts_a_node[1].name,
                    "description": "Peter",
                    "children": [{
                        "id": subaccounts_a_b_node[0].pk,
                        "name": subaccounts_a_b_node[0].name,
                        "identifier": "Sub Account A-B-A",
                        "type": "subaccount",
                        "description": "Jack",
                        "children": []
                    }]
                },
                {
                    "id": subaccounts_a_node[2].pk,
                    "identifier": "Sub Account A-C",
                    "type": "subaccount",
                    "name": subaccounts_a_node[2].name,
                    "description": "Jack",
                    "children": []
                }
            ]
        },
        {
            "id": accounts[1].pk,
            "identifier": "Account B",
            "type": "account",
            "description": accounts[1].description,
            "children": [
                {
                    "id": subaccounts_b_node[0].pk,
                    "identifier": "Sub Account B-A",
                    "type": "subaccount",
                    "name": subaccounts_b_node[0].name,
                    "description": "Jack",
                    "children": []
                }
            ]
        },
        {
            "id": accounts[2].pk,
            "identifier": "Account Jack",
            "type": "account",
            "description": accounts[2].description,
            "children": []
        }
    ]
