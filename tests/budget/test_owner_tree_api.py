from greenbudget.app import signals


def test_get_owner_tree(api_client, user, create_budget, create_markup,
        create_budget_account, create_budget_subaccount):
    with signals.disable():
        markups = []
        budget = create_budget()
        markups = [
            create_markup(
                parent=budget,
                identifier='Not in Search',
                description='Also not in search.'
            ),
            create_markup(
                parent=budget,
                identifier='jack 100',
                description='description'
            )
        ]
        accounts = [
            create_budget_account(parent=budget, identifier="Account A"),
            create_budget_account(
                parent=budget,
                identifier="Account B",
                markups=[markups[0]]
            ),
        ]
        markups.append(create_markup(parent=accounts[0]))
        first_level_subaccounts = [
            create_budget_subaccount(
                parent=accounts[0],
                markups=[markups[1]],
                identifier="Sub Account A-A"
            ),
            create_budget_subaccount(
                parent=accounts[0],
                identifier="Sub Account A-B"
            ),
            create_budget_subaccount(
                parent=accounts[0],
                identifier="Sub Account A-C"
            ),
            create_budget_subaccount(
                parent=accounts[0],
                identifier="Sub Account A-D"
            )
        ]
        markups.append(create_markup(parent=first_level_subaccounts[0]))
        second_level_subaccounts = [
            create_budget_subaccount(
                parent=first_level_subaccounts[0],
                identifier="Sub Account A-A-A",
                markups=[markups[2]]
            ),
            create_budget_subaccount(
                parent=first_level_subaccounts[1],
                identifier="Sub Account A-B-A"
            ),
            create_budget_subaccount(
                parent=first_level_subaccounts[1],
                identifier="Sub Account A-B-B"
            ),
            create_budget_subaccount(
                parent=first_level_subaccounts[2],
                identifier="Sub Account A-C-A"
            ),
            create_budget_subaccount(
                parent=first_level_subaccounts[2],
                identifier="Sub Account A-C-B"
            ),
            create_budget_subaccount(
                parent=first_level_subaccounts[2],
                identifier="Sub Account A-C-C"
            )
        ]
    api_client.force_login(user)
    response = api_client.get(
        "/v1/budgets/%s/subaccounts/owner-tree/" % budget.pk)
    assert response.status_code == 200

    assert response.json()['count'] == 7

    assert response.json()['data'] == [
        {
            "id": markups[2].pk,
            "identifier": markups[2].identifier,
            "type": "markup",
            "description": markups[2].description,
            "in_search_path": True
        },
        {
            "id": markups[1].pk,
            "identifier": markups[1].identifier,
            "type": "markup",
            "description": markups[1].description,
            "in_search_path": True
        },
        {
            "id": markups[0].pk,
            "identifier": markups[0].identifier,
            "type": "markup",
            "description": markups[0].description,
            "in_search_path": True
        },
        {
            "id": first_level_subaccounts[0].pk,
            "identifier": "Sub Account A-A",
            "type": "subaccount",
            "description": first_level_subaccounts[0].description,
            "in_search_path": True,
            "children": [
                {
                    "id": markups[3].pk,
                    "identifier": markups[3].identifier,
                    "type": "markup",
                    "description": markups[3].description,
                    "in_search_path": True
                },
                {
                    "id": second_level_subaccounts[0].pk,
                    "identifier": "Sub Account A-A-A",
                    "type": "subaccount",
                    "description": second_level_subaccounts[0].description,
                    "children": [],
                    "in_search_path": True,
                },
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


def test_search_owner_tree(api_client, user, create_budget, create_markup,
        create_budget_account, create_budget_subaccount):
    with signals.disable():
        budget = create_budget()
        markups = [
            create_markup(
                parent=budget,
                identifier='Not in Search',
                description='Also not in search.'
            ),
            create_markup(
                parent=budget,
                identifier='jack 100',
                description='description'
            )
        ]
        accounts = [
            create_budget_account(parent=budget, identifier="Account A"),
            create_budget_account(
                parent=budget,
                identifier="Account B",
                markups=[markups[0]]
            ),
        ]
        markups.append(create_markup(
            parent=accounts[0],
            identifier='Jacklyn',
            description='description'
        ))
        first_level_subaccounts = [
            create_budget_subaccount(
                parent=accounts[0],
                identifier="Sub Account A-A",
                description="Jack",
            ),
            create_budget_subaccount(
                parent=accounts[0],
                identifier="Sub Account A-B",
                description="Jacky",
            ),
            create_budget_subaccount(
                parent=accounts[0],
                identifier="Sub Account A-C",
                description='description'
            ),
            create_budget_subaccount(
                parent=accounts[0],
                identifier="Sub Account A-D",
                description='description'
            )
        ]
        markups.append(create_markup(
            parent=first_level_subaccounts[0],
            identifier='Jack in search',
            description='description'
        ))
        second_level_subaccounts = [
            create_budget_subaccount(
                parent=first_level_subaccounts[0],
                identifier="Sub Account A-A-A",
                description='description'
            ),
            create_budget_subaccount(
                parent=first_level_subaccounts[1],
                identifier="Sub Account A-B-A",
                description="Jack",
            ),
            create_budget_subaccount(
                parent=first_level_subaccounts[1],
                identifier="Sub Account A-B-B",
                description='description'
            ),
            create_budget_subaccount(
                parent=first_level_subaccounts[2],
                identifier="Sub Account A-C-A",
                description='description'
            ),
            create_budget_subaccount(
                parent=first_level_subaccounts[2],
                identifier="Sub Account A-C-B",
                description="Jack"
            ),
            create_budget_subaccount(
                parent=first_level_subaccounts[2],
                identifier="Sub Account A-C-C",
                description='description'
            )
        ]
    api_client.force_login(user)
    response = api_client.get(
        "/v1/budgets/%s/subaccounts/owner-tree/?search=jack" % budget.pk)
    assert response.status_code == 200

    assert response.json()['count'] == 5

    assert response.json()['data'] == [
        {
            "id": markups[2].pk,
            "identifier": 'Jacklyn',
            "type": "markup",
            "description": 'description',
            "in_search_path": True
        },
        {
            "id": markups[1].pk,
            "identifier": 'jack 100',
            "type": "markup",
            "description": 'description',
            "in_search_path": True
        },
        {
            "id": first_level_subaccounts[0].pk,
            "identifier": "Sub Account A-A",
            "type": "subaccount",
            "description": "Jack",
            "in_search_path": True,
            "children": [
                {
                    "id": markups[3].pk,
                    "identifier": "Jack in search",
                    "type": "markup",
                    "description": "description",
                    "in_search_path": True
                },
            ]
        },
        {
            "id": first_level_subaccounts[1].pk,
            "identifier": "Sub Account A-B",
            "type": "subaccount",
            "description": "Jacky",
            "in_search_path": True,
            "children": [
                {
                    "id": second_level_subaccounts[1].pk,
                    "identifier": "Sub Account A-B-A",
                    "type": "subaccount",
                    "description": "Jack",
                    "children": [],
                    "in_search_path": True,
                }
            ]
        },
        {
            "id": first_level_subaccounts[2].pk,
            "identifier": "Sub Account A-C",
            "type": "subaccount",
            "description": "description",
            "in_search_path": False,
            "children": [
                {
                    "id": second_level_subaccounts[4].pk,
                    "identifier": "Sub Account A-C-B",
                    "type": "subaccount",
                    "description": "Jack",
                    "children": [],
                    "in_search_path": True,
                }
            ]
        }
    ]
