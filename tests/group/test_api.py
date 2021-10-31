import pytest


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_get_account_group(api_client, user, create_account, create_group,
        create_context_budget, context):
    budget = create_context_budget(context=context)
    group = create_group(parent=budget)
    account = create_account(parent=budget, group=group, context=context)
    api_client.force_login(user)
    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": group.pk,
        "type": "group",
        "name": group.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [account.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_get_subaccount_group(api_client, user, create_account, create_group,
        context, create_subaccount, create_context_budget):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    group = create_group(parent=account)
    subaccount = create_subaccount(
        parent=account,
        group=group,
        context=context
    )
    api_client.force_login(user)
    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": group.pk,
        "type": "group",
        "name": group.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": None,
        "updated_by": user.pk,
        "created_by": user.pk,
        "children": [subaccount.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_account_group(api_client, user, create_group, create_account,
        create_context_budget, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
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
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [account.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_subaccount_group(api_client, user, create_account, create_group,
        create_subaccount, create_context_budget, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
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
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": None,
        "updated_by": user.pk,
        "created_by": user.pk,
        "children": [subaccount.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_remove_subaccount_group_children(api_client, user, create_account,
        create_group, create_subaccount, create_context_budget, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    group = create_group(parent=account)
    subaccounts = [
        create_subaccount(
            parent=account,
            context=context,
            group=group
        ),
        create_subaccount(
            parent=account,
            context=context,
            group=group
        )
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
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": None,
        "updated_by": user.pk,
        "created_by": user.pk,
        "children": [subaccounts[0].pk]
    }


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_account_group_child_not_same_parent(api_client, user,
        create_account, create_context_budget, create_group, context):
    budget = create_context_budget(context=context)
    another_budget = create_context_budget(context=context)
    account = create_account(parent=another_budget, context=context)
    group = create_group(parent=budget)
    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [account.pk],
    })
    assert response.status_code == 400


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_subaccount_group_child_not_same_parent(api_client, context,
        user, create_subaccount, create_account, create_context_budget,
        create_group):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)

    another_account = create_account(parent=budget, context=context)
    group = create_group(parent=another_account)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [subaccount.pk],
    })
    assert response.status_code == 400
    assert response.json()['errors'][0]['code'] == 'does_not_exist'


@pytest.mark.parametrize('context', ['budget'])
def test_account_group_account_already_in_group(api_client, user, context,
        create_account, create_context_budget, create_group, models):
    budget = create_context_budget(context=context)
    group = create_group(parent=budget)
    account = create_account(parent=budget, group=group, context=context)
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


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_subaccount_group_account_already_in_group(api_client, user, context,
        create_account, create_context_budget, create_group, models,
        create_subaccount):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    group = create_group(parent=account)
    subaccount = create_subaccount(parent=account, group=group, context=context)
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


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_delete_account_group(api_client, user, create_context_budget, models,
        create_group, context):
    budget = create_context_budget(context=context)
    group = create_group(parent=budget)

    api_client.force_login(user)
    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert models.Group.objects.count() == 0


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_delete_subaccount_group(api_client, user, create_account, context,
        create_context_budget, create_group, models):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    group = create_group(parent=account)

    api_client.force_login(user)
    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert models.Group.objects.count() == 0
