def test_get_budget_account_subaccount_groups(api_client, user, f, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    subaccount = budget_f.create_subaccount(
        parent=account,
        group=group,

    )
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
        "id": group.pk,
        "name": group.name,
        "type": "group",
        "color": group.color,
        "children": [subaccount.pk]
    }]


def test_create_account_subaccount_group(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)

    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/groups/" % account.pk, data={
        'name': 'Group Name',
        'children': [subaccount.pk],
        'color': '#a1887f',
    })
    assert response.status_code == 201
    group = models.Group.objects.first()
    assert group is not None
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == subaccount
    assert group.parent == account

    assert response.json() == {
        "id": 1,
        "name": "Group Name",
        "type": "group",
        "color": '#a1887f',
        "children": [subaccount.pk]
    }


def test_create_account_subaccount_group_invalid_child(api_client, user,
        budget_f):
    budget = budget_f.create_budget()
    # We are trying to create the grouping under `account` but
    # including children that belong to `another_account`, which should
    # trigger a 400 response.
    account = budget_f.create_account(parent=budget)
    another_account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=another_account)

    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/groups/" % account.pk, data={
        'name': 'Group Name',
        'children': [subaccount.pk],
        'color': '#a1887f',
    })
    assert response.status_code == 400
