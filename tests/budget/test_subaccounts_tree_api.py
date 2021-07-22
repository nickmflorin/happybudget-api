from greenbudget.app import signals


def test_get_subaccounts_tree(api_client, user, create_budget,
        create_budget_account, create_budget_subaccount):
    with signals.disable():
        budget = create_budget()
        accounts = [
            create_budget_account(budget=budget, identifier="Account A"),
            create_budget_account(budget=budget, identifier="Account B"),
        ]
        first_level_subaccounts = [
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
            ),
            create_budget_subaccount(
                budget=budget,
                parent=accounts[0],
                identifier="Sub Account A-D"
            )
        ]
        second_level_subaccounts = [
            create_budget_subaccount(
                budget=budget,
                parent=first_level_subaccounts[0],
                identifier="Sub Account A-A-A"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=first_level_subaccounts[1],
                identifier="Sub Account A-B-A"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=first_level_subaccounts[1],
                identifier="Sub Account A-B-B"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=first_level_subaccounts[2],
                identifier="Sub Account A-C-A"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=first_level_subaccounts[2],
                identifier="Sub Account A-C-B"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=first_level_subaccounts[2],
                identifier="Sub Account A-C-C"
            )
        ]
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/subaccounts/tree/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 4
    assert response.json()['data'] == [
        {
            "id": first_level_subaccounts[0].pk,
            "identifier": "Sub Account A-A",
            "type": "subaccount",
            "description": first_level_subaccounts[0].description,
            "in_search_path": True,
            "children": [
                {
                    "id": second_level_subaccounts[0].pk,
                    "identifier": "Sub Account A-A-A",
                    "type": "subaccount",
                    "description": second_level_subaccounts[0].description,
                    "children": [],
                    "in_search_path": True,
                }
            ]
        },
        {
            "id": first_level_subaccounts[1].pk,
            "identifier": "Sub Account A-B",
            "type": "subaccount",
            "description": first_level_subaccounts[1].description,
            "in_search_path": True,
            "children": [
                {
                    "id": second_level_subaccounts[1].pk,
                    "identifier": "Sub Account A-B-A",
                    "type": "subaccount",
                    "description": second_level_subaccounts[1].description,
                    "children": [],
                    "in_search_path": True,
                },
                {
                    "id": second_level_subaccounts[2].pk,
                    "identifier": "Sub Account A-B-B",
                    "type": "subaccount",
                    "description": second_level_subaccounts[2].description,
                    "children": [],
                    "in_search_path": True,
                }
            ]
        },
        {
            "id": first_level_subaccounts[2].pk,
            "identifier": "Sub Account A-C",
            "type": "subaccount",
            "description": first_level_subaccounts[2].description,
            "in_search_path": True,
            "children": [
                {
                    "id": second_level_subaccounts[3].pk,
                    "identifier": "Sub Account A-C-A",
                    "type": "subaccount",
                    "description": second_level_subaccounts[3].description,
                    "children": [],
                    "in_search_path": True,
                },
                {
                    "id": second_level_subaccounts[4].pk,
                    "identifier": "Sub Account A-C-B",
                    "type": "subaccount",
                    "description": second_level_subaccounts[4].description,
                    "children": [],
                    "in_search_path": True,
                },
                {
                    "id": second_level_subaccounts[5].pk,
                    "identifier": "Sub Account A-C-C",
                    "type": "subaccount",
                    "description": second_level_subaccounts[5].description,
                    "children": [],
                    "in_search_path": True,
                }
            ]
        },
        {
            "id": first_level_subaccounts[3].pk,
            "identifier": "Sub Account A-D",
            "type": "subaccount",
            "description": first_level_subaccounts[3].description,
            "in_search_path": True,
            "children": []
        }
    ]


def test_search_subaccounts_tree(api_client, user, create_budget,
        create_budget_account, create_budget_subaccount):
    with signals.disable():
        budget = create_budget()
        accounts = [
            create_budget_account(budget=budget, identifier="Account A"),
            create_budget_account(budget=budget, identifier="Account B"),
        ]
        first_level_subaccounts = [
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
                description="Jacky",
            ),
            create_budget_subaccount(
                budget=budget,
                parent=accounts[0],
                identifier="Sub Account A-C"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=accounts[0],
                identifier="Sub Account A-D"
            )
        ]
        second_level_subaccounts = [
            create_budget_subaccount(
                budget=budget,
                parent=first_level_subaccounts[0],
                identifier="Sub Account A-A-A",
                description="Mufassa"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=first_level_subaccounts[1],
                identifier="Sub Account A-B-A",
                description="Jack",
            ),
            create_budget_subaccount(
                budget=budget,
                parent=first_level_subaccounts[1],
                identifier="Sub Account A-B-B",
                description="Banana"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=first_level_subaccounts[2],
                identifier="Sub Account A-C-A",
                description="Banana"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=first_level_subaccounts[2],
                identifier="Sub Account A-C-B",
                description="Jack"
            ),
            create_budget_subaccount(
                budget=budget,
                parent=first_level_subaccounts[2],
                identifier="Sub Account A-C-C",
                description="Banana"
            )
        ]
    api_client.force_login(user)
    response = api_client.get(
        "/v1/budgets/%s/subaccounts/tree/?search=jack" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 3
    assert response.json()['data'] == [
        {
            "id": first_level_subaccounts[0].pk,
            "identifier": "Sub Account A-A",
            "type": "subaccount",
            "description": first_level_subaccounts[0].description,
            "in_search_path": True,
            "children": []
        },
        {
            "id": first_level_subaccounts[1].pk,
            "identifier": "Sub Account A-B",
            "type": "subaccount",
            "description": first_level_subaccounts[1].description,
            "in_search_path": True,
            "children": [
                {
                    "id": second_level_subaccounts[1].pk,
                    "identifier": "Sub Account A-B-A",
                    "type": "subaccount",
                    "description": second_level_subaccounts[1].description,
                    "children": [],
                    "in_search_path": True,
                }
            ]
        },
        {
            "id": first_level_subaccounts[2].pk,
            "identifier": "Sub Account A-C",
            "type": "subaccount",
            "description": first_level_subaccounts[2].description,
            "in_search_path": False,
            "children": [
                {
                    "id": second_level_subaccounts[4].pk,
                    "identifier": "Sub Account A-C-B",
                    "type": "subaccount",
                    "description": second_level_subaccounts[4].description,
                    "children": [],
                    "in_search_path": True,
                }
            ]
        }
    ]
