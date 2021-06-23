import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_account_groups(api_client, user,
        create_budget_account, create_budget, create_budget_account_group):
    budget = create_budget()
    group = create_budget_account_group(parent=budget)
    account = create_budget_account(budget=budget, group=group)
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/groups/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
        "id": group.pk,
        "name": group.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": group.color,
        "updated_by": user.pk,
        "actual": 0.0,
        "variance": 0.0,
        "estimated": 0.0,
        "created_by": user.pk,
        "children": [account.pk]
    }]


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_account_group(api_client, user, create_budget_account,
        create_budget, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)

    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/groups/" % budget.pk, data={
        'name': 'Group Name',
        'children': [account.pk],
        'color': '#a1887f'
    })
    assert response.status_code == 201

    group = models.BudgetAccountGroup.objects.first()
    assert group is not None
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == account
    assert group.parent == budget

    assert response.json() == {
        "id": group.pk,
        "name": "Group Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": '#a1887f',
        "updated_by": None,
        "actual": 0.0,
        "variance": 0.0,
        "estimated": 0.0,
        "created_by": user.pk,
        "children": [account.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_account_group_invalid_child(api_client, user,
        create_budget_account, create_budget):
    budget = create_budget()
    another_budget = create_budget()
    # We are trying to create the grouping under `budget` but including children
    # that belong to `another_budget`, which should trigger a 400 response.
    account = create_budget_account(budget=another_budget)

    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/groups/" % budget.pk, data={
        'name': 'Group Name',
        'children': [account.pk],
        'color': '#a1887f',
    })
    assert response.status_code == 400
