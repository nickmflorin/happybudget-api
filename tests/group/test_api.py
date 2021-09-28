import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_account_group(api_client, user, create_budget_account,
        create_budget, create_group):
    budget = create_budget()
    group = create_group(parent=budget)
    account = create_budget_account(parent=budget, group=group)
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
def test_get_template_account_group(api_client, user, create_template,
        create_template_account, create_group):
    template = create_template()
    group = create_group(parent=template)
    account = create_template_account(parent=template, group=group)
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
def test_get_budget_subaccount_group(api_client, user, create_budget_account,
        create_budget_subaccount, create_budget, create_group):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    group = create_group(parent=account)
    subaccount = create_budget_subaccount(
        parent=account,
        group=group
    )
    api_client.force_login(user)
    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
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
def test_get_template_subaccount_group(api_client, user, create_template,
        create_template_subaccount, create_template_account, create_group):
    template = create_template()
    account = create_template_account(parent=template)
    group = create_group(parent=account)
    subaccount = create_template_subaccount(
        parent=account,
        group=group
    )
    api_client.force_login(user)
    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
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
def test_update_budget_account_group(api_client, user, create_group,
        create_budget_account, create_budget):
    budget = create_budget()
    account = create_budget_account(parent=budget)
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
def test_update_template_account_group(api_client, user, create_template,
        create_template_account, create_group):
    template = create_template()
    account = create_template_account(parent=template)
    group = create_group(name="Group Name", parent=template)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'name': 'Group Name',
        'children': [account.pk],
    })
    group.refresh_from_db()
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == account
    assert group.parent == template

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
def test_update_budget_subaccount_group(api_client, user, create_budget_account,
        create_budget_subaccount, create_budget, create_group):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)
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
        "id": 1,
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
def test_update_template_subaccount_group(api_client, user, create_template,
        create_template_subaccount, create_template_account, create_group):
    template = create_template()
    account = create_template_account(parent=template)
    subaccount = create_template_subaccount(parent=account)
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
        "id": 1,
        "type": "group",
        "name": "Group Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": None,
        "updated_by": user.pk,
        "created_by": user.pk,
        "children": [subaccount.pk]
    }


def test_update_budget_account_group_child_not_same_parent(api_client, user,
        create_budget_account, create_budget, create_group):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(parent=another_budget)
    group = create_group(parent=budget)
    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [account.pk],
    })
    assert response.status_code == 400


def test_update_template_account_group_child_not_same_parent(api_client,
        create_group, create_template_account, create_template, user):
    template = create_template()
    another_template = create_template()
    account = create_template_account(parent=another_template)
    group = create_group(parent=template)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [account.pk],
    })
    assert response.status_code == 400


def test_update_budget_subaccount_group_child_not_same_parent(api_client,
        user, create_budget_subaccount, create_budget_account, create_budget,
        create_group):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)

    another_account = create_budget_account(parent=budget)
    group = create_group(parent=another_account)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [subaccount.pk],
    })
    assert response.status_code == 400
    assert response.json()['errors'][0]['code'] == 'does_not_exist'


def test_update_template_subaccount_group_child_not_same_parent(api_client,
        user, create_template_subaccount, create_template_account,
        create_template, create_group):
    template = create_template()
    account = create_template_account(parent=template)
    subaccount = create_template_subaccount(parent=account)

    another_account = create_template_account(parent=template)
    group = create_group(parent=another_account)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [subaccount.pk],
    })
    assert response.status_code == 400
    assert response.json()['errors'][0]['code'] == 'does_not_exist'


def test_budget_account_group_account_already_in_group(api_client, user,
        create_budget_account, create_budget, create_group, models):
    budget = create_budget()
    group = create_group(parent=budget)
    account = create_budget_account(parent=budget, group=group)
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


def test_template_account_group_account_already_in_group(api_client, user,
        create_template_account, create_template, models, create_group):
    template = create_template()
    group = create_group(parent=template)
    account = create_template_account(parent=template, group=group)
    another_group = create_group(parent=template)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % another_group.pk, data={
        'children': [account.pk]
    })
    assert response.status_code == 200
    account.refresh_from_db()
    assert account.group == another_group
    # The group should be deleted since it has become empty.
    assert models.Group.objects.count() == 1


def test_budget_subaccount_group_account_already_in_group(api_client, user,
        create_budget_account, create_budget, create_group, models,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    group = create_group(parent=account)
    subaccount = create_budget_subaccount(parent=account, group=group)
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


def test_template_subaccount_group_account_already_in_group(api_client, user,
        create_template_account, create_template, create_template_subaccount,
        create_group, models):
    template = create_template()
    account = create_template_account(parent=template)
    group = create_group(parent=account)
    subaccount = create_template_subaccount(parent=account, group=group)
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


def test_delete_budget_account_group(api_client, user, create_budget, models,
        create_group):
    budget = create_budget()
    group = create_group(parent=budget)

    api_client.force_login(user)
    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert models.Group.objects.count() == 0


def test_delete_template_account_group(api_client, user, create_template,
        create_group, models):
    template = create_template()
    group = create_group(parent=template)

    api_client.force_login(user)
    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert models.Group.objects.count() == 0


def test_delete_budget_subaccount_group(api_client, user, create_budget_account,
        create_budget, create_group, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    group = create_group(parent=account)

    api_client.force_login(user)
    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert models.Group.objects.count() == 0


def test_delete_template_subaccount_group(api_client, user, create_template,
        create_template_account, create_group, models):
    template = create_template()
    account = create_template_account(parent=template)
    group = create_group(parent=account)

    api_client.force_login(user)
    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert models.Group.objects.count() == 0
