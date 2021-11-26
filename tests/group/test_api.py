def test_get_account_group(api_client, user, budget_f, create_group):
    budget = budget_f.create_budget()
    group = create_group(parent=budget)
    account = budget_f.create_account(parent=budget, group=group)
    api_client.force_login(user)
    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": group.pk,
        "type": "group",
        "name": group.name,
        "color": None,
        "children": [account.pk]
    }


def test_get_subaccount_group(api_client, user, budget_f, create_group):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = create_group(parent=account)
    subaccount = budget_f.create_subaccount(parent=account, group=group)
    api_client.force_login(user)
    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": group.pk,
        "type": "group",
        "name": group.name,
        "color": None,
        "children": [subaccount.pk]
    }


def test_update_account_group(api_client, user, create_group, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = create_group(name="Group Name", parent=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'name': 'Group Name',
        'children': [account.pk]
    })
    group.refresh_from_db()
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == account
    assert group.parent == budget

    assert response.json() == {
        "id": group.pk,
        "type": "group",
        "name": "Group Name",
        "color": None,
        "children": [account.pk]
    }


def test_update_subaccount_group(api_client, user, budget_f, create_group):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    group = create_group(parent=account)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'name': 'Group Name',
        'children': [subaccount.pk]
    })
    assert response.status_code == 200

    group.refresh_from_db()
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == subaccount
    assert group.parent == account

    assert response.json() == {
        "id": group.pk,
        "type": "group",
        "name": "Group Name",
        "color": None,
        "children": [subaccount.pk]
    }


def test_remove_subaccount_group_children(api_client, user, budget_f,
        create_group):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = create_group(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=account, group=group),
        budget_f.create_subaccount(parent=account, group=group)
    ]
    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [subaccounts[0].pk]
    })
    assert response.status_code == 200

    group.refresh_from_db()
    assert group.children.count() == 1
    assert group.children.first() == subaccounts[0]
    assert group.parent == account

    assert response.json() == {
        "id": group.pk,
        "type": "group",
        "name": group.name,
        "color": None,
        "children": [subaccounts[0].pk]
    }


def test_update_account_group_child_not_same_parent(api_client, user, budget_f,
        create_group):
    budget = budget_f.create_budget()
    another_budget = budget_f.create_budget()
    account = budget_f.create_account(parent=another_budget)
    group = create_group(parent=budget)
    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [account.pk],
    })
    assert response.status_code == 400


def test_update_subaccount_group_child_not_same_parent(api_client, budget_f,
        user, create_group):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)

    another_account = budget_f.create_account(parent=budget)
    group = create_group(parent=another_account)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [subaccount.pk],
    })
    assert response.status_code == 400
    assert response.json()['errors'][0]['code'] == 'does_not_exist'


def test_account_group_account_already_in_group(api_client, user, budget_df,
        create_group, models):
    budget = budget_df.create_budget()
    group = create_group(parent=budget)
    account = budget_df.create_account(parent=budget, group=group)
    another_group = create_group(parent=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % another_group.pk, data={
        'children': [account.pk]
    })
    assert response.status_code == 200
    account.refresh_from_db()
    assert account.group == another_group
    # The group should be deleted since it has become empty.
    assert models.Group.objects.count() == 1


def test_subaccount_group_account_already_in_group(api_client, user, budget_f,
        create_group, models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = create_group(parent=account)
    subaccount = budget_f.create_subaccount(parent=account, group=group)
    another_group = create_group(parent=account)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % another_group.pk, data={
        'children': [subaccount.pk]
    })
    assert response.status_code == 200
    subaccount.refresh_from_db()
    assert subaccount.group == another_group
    # The group should be deleted since it has become empty.
    assert models.Group.objects.count() == 1


def test_delete_account_group(api_client, user, budget_f, models, create_group):
    budget = budget_f.create_budget()
    group = create_group(parent=budget)

    api_client.force_login(user)
    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert models.Group.objects.count() == 0


def test_delete_subaccount_group(api_client, user, budget_f, create_group,
        models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = create_group(parent=account)

    api_client.force_login(user)
    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert models.Group.objects.count() == 0
