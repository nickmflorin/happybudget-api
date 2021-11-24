def test_get_actual_owners(api_client, user, create_budget, create_markup,
        create_budget_account, create_budget_subaccount):
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
            markups=[markups[2]],
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
            markups=[markups[3]]
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
    response = api_client.get("/v1/budgets/%s/actual-owners/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 14
    assert response.json()['data'] == [
        {
            "id": first_level_subaccounts[0].pk,
            "identifier": "Sub Account A-A",
            "type": "subaccount",
            "description": first_level_subaccounts[0].description,
        },
        {
            "id": second_level_subaccounts[0].pk,
            "identifier": "Sub Account A-A-A",
            "type": "subaccount",
            "description": second_level_subaccounts[0].description,
        },
        {
            "id": second_level_subaccounts[1].pk,
            "identifier": "Sub Account A-B-A",
            "type": "subaccount",
            "description": second_level_subaccounts[1].description,
        },
        {
            "id": second_level_subaccounts[3].pk,
            "identifier": "Sub Account A-C-A",
            "type": "subaccount",
            "description": second_level_subaccounts[3].description,
        },
        {
            "id": first_level_subaccounts[1].pk,
            "identifier": "Sub Account A-B",
            "type": "subaccount",
            "description": first_level_subaccounts[1].description,
        },
        {
            "id": second_level_subaccounts[2].pk,
            "identifier": "Sub Account A-B-B",
            "type": "subaccount",
            "description": second_level_subaccounts[2].description,
        },
        {
            "id": second_level_subaccounts[4].pk,
            "identifier": "Sub Account A-C-B",
            "type": "subaccount",
            "description": second_level_subaccounts[4].description,
        },
        {
            "id": first_level_subaccounts[2].pk,
            "identifier": "Sub Account A-C",
            "type": "subaccount",
            "description": first_level_subaccounts[2].description,
        },
        {
            "id": second_level_subaccounts[5].pk,
            "identifier": "Sub Account A-C-C",
            "type": "subaccount",
            "description": second_level_subaccounts[5].description,
        },
        {
            "id": first_level_subaccounts[3].pk,
            "identifier": "Sub Account A-D",
            "type": "subaccount",
            "description": first_level_subaccounts[3].description,
        },
        {
            "id": markups[0].pk,
            "identifier": markups[0].identifier,
            "type": "markup",
            "description": markups[0].description,
        },
        {
            "id": markups[1].pk,
            "identifier": markups[1].identifier,
            "type": "markup",
            "description": markups[1].description,
        },
        {
            "id": markups[2].pk,
            "identifier": markups[2].identifier,
            "type": "markup",
            "description": markups[2].description,
        },
        {
            "id": markups[3].pk,
            "identifier": markups[3].identifier,
            "type": "markup",
            "description": markups[3].description,
        },
    ]
