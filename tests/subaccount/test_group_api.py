def test_get_subaccount_subaccount_groups(api_client, user, budget_f,
        create_group):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    group = create_group(parent=subaccount)
    child_subaccount = budget_f.create_subaccount(
        parent=subaccount,
        group=group
    )
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/groups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
        "id": group.pk,
        "type": "group",
        "name": group.name,
        "color": group.color,
        "children": [child_subaccount.pk]
    }]


def test_create_subaccount_subaccount_group(api_client, user, budget_f, models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    child_subaccount = budget_f.create_subaccount(parent=subaccount)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/groups/" % subaccount.pk, data={
            'name': 'Group Name',
            'children': [child_subaccount.pk],
            'color': '#a1887f'
        })
    assert response.status_code == 201

    group = models.Group.objects.first()
    assert group is not None
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == child_subaccount
    assert group.parent == subaccount

    assert response.json() == {
        "id": group.pk,
        "type": "group",
        "name": "Group Name",
        "color": '#a1887f',
        "children": [child_subaccount.pk]
    }


def test_create_subaccount_subaccount_group_invalid_child(api_client, user,
        budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    # We are trying to create the grouping under `another_sub_account` but
    # including children that belong to `child_subaccount`, which should
    # trigger a 400 response.
    another_sub_account = budget_f.create_subaccount(parent=account)
    child_subaccount = budget_f.create_subaccount(parent=subaccount)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/groups/" % another_sub_account.pk, data={
            'name': 'Group Name',
            'children': [child_subaccount.pk],
            'color': '#a1887f',
        })
    assert response.status_code == 400
