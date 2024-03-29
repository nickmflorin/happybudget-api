def test_get_budget_groups(api_client, user, f, budget_f):
    budget = budget_f.create_budget()
    group = f.create_group(parent=budget)
    account = budget_f.create_account(parent=budget, group=group)
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/groups/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
        "id": group.pk,
        "type": "group",
        "name": group.name,
        "color": group.color,
        "children": [account.pk]
    }]


def test_create_budget_group(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/groups/" % budget.pk,
        data={
            'name': 'Group Name',
            'children': [account.pk],
            'color': '#a1887f'
        })
    assert response.status_code == 201

    group = models.Group.objects.first()
    assert group is not None
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == account
    assert group.parent == budget

    assert response.json() == {
        "id": group.pk,
        "type": "group",
        "name": "Group Name",
        "color": '#a1887f',
        "children": [account.pk]
    }


def test_create_budget_group_invalid_child(api_client, user, budget_f):
    budget = budget_f.create_budget()
    another_budget = budget_f.create_budget()
    # We are trying to create the grouping under `budget` but including
    # children that belong to `another_budget`, which should trigger a 400
    # response.
    account = budget_f.create_account(parent=another_budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/groups/" % budget.pk,
        data={
            'name': 'Group Name',
            'children': [account.pk],
            'color': '#a1887f',
        })
    assert response.status_code == 400
