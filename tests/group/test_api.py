import pytest

from greenbudget.app.group.models import Group


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_account_group(api_client, user, create_budget_account,
        create_budget, create_budget_account_group):
    budget = create_budget()
    group = create_budget_account_group(parent=budget)
    account = create_budget_account(budget=budget, group=group)

    api_client.force_login(user)
    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": group.pk,
        "name": group.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": '#EFEFEF',
        "actual": None,
        "variance": None,
        "estimated": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [account.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_account_group(api_client, user, create_template,
        create_template_account, create_template_account_group):
    template = create_template()
    group = create_template_account_group(parent=template)
    account = create_template_account(budget=template, group=group)

    api_client.force_login(user)
    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": group.pk,
        "name": group.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": '#EFEFEF',
        "estimated": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [account.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_subaccount_group(api_client, user, create_budget_account,
        create_budget_subaccount, create_budget,
        create_budget_subaccount_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    group = create_budget_subaccount_group(parent=account)
    subaccount = create_budget_subaccount(
        parent=account,
        budget=budget,
        group=group
    )
    api_client.force_login(user)
    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": group.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": '#EFEFEF',
        "actual": None,
        "variance": None,
        "estimated": None,
        "updated_by": user.pk,
        "created_by": user.pk,
        "children": [subaccount.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_subaccount_group(api_client, user, create_template,
        create_template_subaccount, create_template_account,
        create_template_subaccount_group):
    template = create_template()
    account = create_template_account(budget=template)
    group = create_template_subaccount_group(parent=account)
    subaccount = create_template_subaccount(
        parent=account,
        budget=template,
        group=group
    )
    api_client.force_login(user)
    response = api_client.get("/v1/groups/%s/" % group.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": group.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": '#EFEFEF',
        "estimated": None,
        "updated_by": user.pk,
        "created_by": user.pk,
        "children": [subaccount.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget_account_group(api_client, user, create_budget_account,
        create_budget, create_budget_account_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    group = create_budget_account_group(name="Group Name", parent=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'name': 'Group Name',
        'children': [account.pk],
    })
    group.refresh_from_db()
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == account
    assert group.parent == budget

    assert response.json() == {
        "id": group.pk,
        "name": "Group Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": '#EFEFEF',
        "actual": None,
        "variance": None,
        "estimated": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [account.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_template_account_group(api_client, user, create_template,
        create_template_account, create_template_account_group):
    template = create_template()
    account = create_template_account(budget=template)
    group = create_template_account_group(name="Group Name", parent=template)

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
        "name": "Group Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": '#EFEFEF',
        "estimated": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [account.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget_subaccount_group(api_client, user, create_budget_account,
        create_budget_subaccount, create_budget,
        create_budget_subaccount_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)
    group = create_budget_subaccount_group(parent=account)

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
        "name": "Group Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": '#EFEFEF',
        "actual": None,
        "variance": None,
        "estimated": None,
        "updated_by": user.pk,
        "created_by": user.pk,
        "children": [subaccount.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_template_subaccount_group(api_client, user, create_template,
        create_template_subaccount, create_template_account,
        create_template_subaccount_group):
    template = create_template()
    account = create_template_account(budget=template)
    subaccount = create_template_subaccount(parent=account, budget=template)
    group = create_template_subaccount_group(parent=account)

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
        "name": "Group Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": '#EFEFEF',
        "estimated": None,
        "updated_by": user.pk,
        "created_by": user.pk,
        "children": [subaccount.pk]
    }


def test_update_budget_account_group_child_not_same_parent(api_client, user,
        create_budget_account, create_budget, create_budget_account_group):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(budget=another_budget)
    group = create_budget_account_group(parent=budget)
    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [account.pk],
    })
    assert response.status_code == 400


def test_update_template_account_group_child_not_same_parent(api_client,
        create_template_account_group, create_template_account, create_template,
        user):
    template = create_template()
    another_template = create_template()
    account = create_template_account(budget=another_template)
    group = create_template_account_group(parent=template)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [account.pk],
    })
    assert response.status_code == 400


def test_update_budget_subaccount_group_child_not_same_parent(api_client,
        user, create_budget_subaccount, create_budget_account,
        create_budget, create_budget_subaccount_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)

    another_account = create_budget_account(budget=budget)
    group = create_budget_subaccount_group(parent=another_account)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [subaccount.pk],
    })
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'code': 'invalid',
            'error_type': 'field',
            'field': 'children',
            'message': (
                'The BudgetSubAccount %s does not belong to the same '
                'BudgetAccount that the Group does (%s).'
                % (subaccount.pk, another_account.pk)
            )
        }]
    }


def test_update_template_subaccount_group_child_not_same_parent(api_client,
        user, create_template_subaccount, create_template_account,
        create_template, create_template_subaccount_group):
    template = create_template()
    account = create_template_account(budget=template)
    subaccount = create_template_subaccount(parent=account, budget=template)

    another_account = create_template_account(budget=template)
    group = create_template_subaccount_group(parent=another_account)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'children': [subaccount.pk],
    })
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'code': 'invalid',
            'error_type': 'field',
            'field': 'children',
            'message': (
                'The TemplateSubAccount %s does not belong to the same '
                'TemplateAccount that the Group does (%s).'
                % (subaccount.pk, another_account.pk)
            )
        }]
    }


def test_update_budget_account_group_duplicate_name(api_client, user,
        create_budget_account, create_budget, create_budget_account_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    create_budget_account_group(name="Group Name", parent=budget)
    group = create_budget_account_group(parent=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'name': 'Group Name',
        'children': [account.pk],
    })
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': 'The fields name must make a unique set.',
            'code': 'unique',
            'error_type': 'field',
            'field': 'name'
        }]
    }


def test_update_template_account_group_duplicate_name(api_client, user,
        create_template_account, create_template,
        create_template_account_group):
    budget = create_template()
    account = create_template_account(budget=budget)
    create_template_account_group(name="Group Name", parent=budget)
    group = create_template_account_group(parent=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'name': 'Group Name',
        'children': [account.pk],
    })
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': 'The fields name must make a unique set.',
            'code': 'unique',
            'error_type': 'field',
            'field': 'name'
        }]
    }


def test_update_budget_subaccount_group_duplicate_name(api_client, user,
        create_budget_subaccount, create_budget_account, create_budget,
        create_budget_subaccount_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)
    create_budget_subaccount_group(parent=account, name="Group Name")
    group = create_budget_subaccount_group(parent=account)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'name': 'Group Name',
        'children': [subaccount.pk]
    })
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': 'The fields name must make a unique set.',
            'code': 'unique',
            'error_type': 'field',
            'field': 'name'
        }]
    }


def test_update_template_subaccount_group_duplicate_name(api_client, user,
        create_template_subaccount, create_template_account, create_template,
        create_template_subaccount_group):
    template = create_template()
    account = create_template_account(budget=template)
    subaccount = create_template_subaccount(parent=account, budget=template)
    create_template_subaccount_group(parent=account, name="Group Name")
    group = create_template_subaccount_group(parent=account)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, data={
        'name': 'Group Name',
        'children': [subaccount.pk]
    })
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': 'The fields name must make a unique set.',
            'code': 'unique',
            'error_type': 'field',
            'field': 'name'
        }]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_budget_account_group_account_already_in_group(api_client, user,
        create_budget_account, create_budget, create_budget_account_group):
    budget = create_budget()
    group = create_budget_account_group(parent=budget)
    account = create_budget_account(budget=budget, group=group)
    another_group = create_budget_account_group(parent=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % another_group.pk, data={
        'children': [account.pk]
    })
    assert response.status_code == 200
    account.refresh_from_db()
    assert account.group == another_group
    group.refresh_from_db()
    assert group.children.count() == 0


@pytest.mark.freeze_time('2020-01-01')
def test_template_account_group_account_already_in_group(api_client, user,
        create_template_account, create_template,
        create_template_account_group):
    template = create_template()
    group = create_template_account_group(parent=template)
    account = create_template_account(budget=template, group=group)
    another_group = create_template_account_group(parent=template)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % another_group.pk, data={
        'children': [account.pk]
    })
    assert response.status_code == 200
    account.refresh_from_db()
    assert account.group == another_group
    group.refresh_from_db()
    assert group.children.count() == 0


def test_delete_budget_account_group(api_client, user, create_budget,
        create_budget_account_group):
    budget = create_budget()
    group = create_budget_account_group(parent=budget)

    api_client.force_login(user)
    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert Group.objects.count() == 0


def test_delete_template_account_group(api_client, user, create_template,
        create_template_account_group):
    template = create_template()
    group = create_template_account_group(parent=template)

    api_client.force_login(user)
    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert Group.objects.count() == 0


def test_delete_budget_subaccount_group(api_client, user, create_budget_account,
        create_budget, create_budget_subaccount_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    group = create_budget_subaccount_group(parent=account)

    api_client.force_login(user)
    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert Group.objects.count() == 0


def test_delete_template_subaccount_group(api_client, user, create_template,
        create_template_account, create_template_subaccount_group):
    template = create_template()
    account = create_template_account(budget=template)
    group = create_template_subaccount_group(parent=account)

    api_client.force_login(user)
    response = api_client.delete("/v1/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert Group.objects.count() == 0
