def test_get_actual_owners(api_client, user, f):
    markups = []
    budget = f.create_budget()
    markups = [
        f.create_markup(
            parent=budget,
            identifier='Not in Search',
            description='Also not in search.'
        ),
        f.create_markup(
            parent=budget,
            identifier='jack 100',
            description='description'
        )
    ]
    accounts = [
        f.create_account(parent=budget, identifier="Account A"),
        f.create_account(
            parent=budget,
            identifier="Account B",
            markups=[markups[0]]
        ),
    ]
    markups.append(f.create_markup(parent=accounts[0]))
    first_level_subaccounts = [
        f.create_subaccount(
            parent=accounts[0],
            markups=[markups[2]],
            identifier="Sub Account A-A"
        ),
        f.create_subaccount(
            parent=accounts[0],
            identifier="Sub Account A-B"
        ),
        f.create_subaccount(
            parent=accounts[0],
            identifier="Sub Account A-C"
        ),
        f.create_subaccount(
            parent=accounts[0],
            identifier="Sub Account A-D"
        )
    ]
    markups.append(f.create_markup(parent=first_level_subaccounts[0]))
    second_level_subaccounts = [
        f.create_subaccount(
            parent=first_level_subaccounts[0],
            identifier="Sub Account A-A-A",
            markups=[markups[3]]
        ),
        f.create_subaccount(
            parent=first_level_subaccounts[1],
            identifier="Sub Account A-B-A"
        ),
        f.create_subaccount(
            parent=first_level_subaccounts[1],
            identifier="Sub Account A-B-B"
        ),
        f.create_subaccount(
            parent=first_level_subaccounts[2],
            identifier="Sub Account A-C-A"
        ),
        f.create_subaccount(
            parent=first_level_subaccounts[2],
            identifier="Sub Account A-C-B"
        ),
        f.create_subaccount(
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
