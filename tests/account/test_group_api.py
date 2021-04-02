import pytest

from greenbudget.app.account.models import AccountGroup


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_account_group(api_client, user, create_account,
        create_budget):
    budget = create_budget()
    account = create_account(budget=budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/groups/" % budget.pk, data={
            'name': 'Group Name',
            'children': [account.pk],
            'color': '#a1887f'
        })
    assert response.status_code == 201

    group = AccountGroup.objects.first()
    assert group is not None
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == account
    assert group.budget == budget

    assert response.json() == {
        "id": group.pk,
        "name": "Group Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": '#a1887f',
        "updated_by": None,
        "actual": None,
        "variance": None,
        "estimated": None,
        "created_by": user.pk,
        "children": [
            {
                "id": account.pk,
                "identifier": '%s' % account.identifier,
            }
        ]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_account_group_invalid_child(api_client, user,
        create_account, create_budget):
    budget = create_budget()
    another_budget = create_budget()
    # We are trying to create the grouping under `budget` but
    # including children that belong to `another_budget`, which should
    # trigger a 400 response.
    account = create_account(budget=another_budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/groups/" % budget.pk, data={
            'name': 'Group Name',
            'children': [account.pk],
            'color': '#a1887f',
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_account_group_duplicate_name(api_client, user,
        create_account, create_budget, create_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    create_account_group(name="Group Name", budget=budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/groups/" % budget.pk, data={
            'name': 'Group Name',
            'children': [account.pk],
            'color': '#a1887f'
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_update_account_group(api_client, user, create_sub_account,
        create_account, create_budget, create_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    group = create_account_group(name="Group Name", budget=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/groups/%s/" % group.pk, data={
            'name': 'Group Name',
            'children': [account.pk],
        })

    group.refresh_from_db()
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == account
    assert group.budget == budget

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
        "children": [
            {
                "id": account.pk,
                "identifier": '%s' % account.identifier,
            }
        ]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_account_group_invalid_child(api_client, user,
        create_account, create_budget, create_account_group):
    budget = create_budget()
    another_budget = create_budget()
    account = create_account(budget=another_budget)
    group = create_account_group(name="Group Name", budget=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/groups/%s/" % group.pk, data={
            'name': 'Group Name',
            'children': [account.pk],
        })

    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_update_account_group_duplicate_name(api_client, user,
        create_account, create_budget, create_account_group):
    budget = create_budget()
    another_budget = create_budget()
    account = create_account(budget=another_budget)
    create_account_group(name="Group Name", budget=budget)
    group = create_account_group(budget=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/groups/%s/" % group.pk, data={
            'name': 'Group Name',
            'children': [account.pk],
        })

    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_group_account_already_in_group(api_client, user,
        create_account, create_budget, create_account_group):
    budget = create_budget()
    group = create_account_group(budget=budget)
    account = create_account(budget=budget, group=group)
    another_group = create_account_group(budget=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/groups/%s/" % another_group.pk, data={
            'children': [account.pk]
        })
    assert response.status_code == 200
    account.refresh_from_db()
    assert account.group == another_group
    group.refresh_from_db()
    assert group.children.count() == 0


@pytest.mark.freeze_time('2020-01-01')
def test_delete_subaccount_group(api_client, user, create_budget,
        create_account_group):
    budget = create_budget()
    group = create_account_group(budget=budget)

    api_client.force_login(user)
    response = api_client.delete("/v1/accounts/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert AccountGroup.objects.count() == 0
