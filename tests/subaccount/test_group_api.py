import pytest

from greenbudget.app.subaccount.models import SubAccountGroup


@pytest.mark.freeze_time('2020-01-01')
def test_create_subaccount_subaccount_group(api_client, user,
        create_sub_account, create_account, create_budget):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(parent=account, budget=budget)
    child_subaccount = create_sub_account(parent=subaccount, budget=budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/groups/" % subaccount.pk, data={
            'name': 'Group Name',
            'children': [child_subaccount.pk],
            'color': '#a1887f'
        })
    assert response.status_code == 201

    group = SubAccountGroup.objects.first()
    assert group is not None
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == child_subaccount
    assert group.parent == subaccount

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
        "created_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name,
            "profile_image": None,
        },
        "children": [
            {
                "id": child_subaccount.pk,
                "name": child_subaccount.name,
                "identifier": '%s' % child_subaccount.identifier
            }
        ]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_subaccount_subaccount_group_invalid_child(api_client, user,
        create_sub_account, create_account, create_budget):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(parent=account, budget=budget)

    # We are trying to create the grouping under `another_sub_account` but
    # including children that belong to `child_subaccount`, which should
    # trigger a 400 response.
    another_sub_account = create_sub_account(parent=account, budget=budget)
    child_subaccount = create_sub_account(parent=subaccount, budget=budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/groups/" % another_sub_account.pk, data={
            'name': 'Group Name',
            'children': [child_subaccount.pk],
            'color': '#a1887f',
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_subaccount_subaccount_group_duplicate_name(api_client, user,
        create_sub_account, create_account, create_budget,
        create_sub_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(parent=account, budget=budget)

    create_sub_account_group(name="Group Name", parent=subaccount)
    child_subaccount = create_sub_account(parent=subaccount, budget=budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/groups/" % subaccount.pk, data={
            'name': 'Group Name',
            'children': [child_subaccount.pk],
            'color': '#a1887f',
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_account_subaccount_group(api_client, user,
        create_sub_account, create_account, create_budget):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(parent=account, budget=budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/accounts/%s/groups/" % account.pk, data={
            'name': 'Group Name',
            'children': [subaccount.pk],
            'color': '#a1887f',
        })
    assert response.status_code == 201

    group = SubAccountGroup.objects.first()
    assert group is not None
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == subaccount
    assert group.parent == account

    assert response.json() == {
        "id": 1,
        "name": "Group Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "updated_by": None,
        "color": '#a1887f',
        "actual": None,
        "variance": None,
        "estimated": None,
        "created_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name,
            "profile_image": None,
        },
        "children": [
            {
                "id": subaccount.pk,
                "name": subaccount.name,
                "identifier": '%s' % subaccount.identifier
            }
        ]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_account_subaccount_group_duplicate_name(api_client, user,
        create_sub_account, create_account, create_budget,
        create_sub_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(parent=account, budget=budget)
    create_sub_account_group(name="Group Name", parent=account)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/groups/" % subaccount.pk, data={
            'name': 'Group Name',
            'children': [subaccount.pk]
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_account_subaccount_group_invalid_child(api_client, user,
        create_sub_account, create_account, create_budget):
    budget = create_budget()

    # We are trying to create the grouping under `account` but
    # including children that belong to `another_account`, which should
    # trigger a 400 response.
    account = create_account(budget=budget)
    another_account = create_account(budget=budget)
    subaccount = create_sub_account(parent=another_account, budget=budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/accounts/%s/groups/" % account.pk, data={
            'name': 'Group Name',
            'children': [subaccount.pk],
            'color': '#a1887f',
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_update_subaccount_group(api_client, user, create_sub_account,
        create_account, create_budget, create_sub_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(parent=account, budget=budget)
    group = create_sub_account_group(parent=account)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/groups/%s/" % group.pk, data={
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
        "updated_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name,
            "profile_image": None,
        },
        "created_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name,
            "profile_image": None,
        },
        "children": [
            {
                "id": subaccount.pk,
                "name": subaccount.name,
                "identifier": '%s' % subaccount.identifier
            }
        ]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_subaccount_group_invalid_child(api_client, user,
        create_sub_account, create_account, create_budget,
        create_sub_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(parent=account, budget=budget)

    another_account = create_account(budget=budget)
    group = create_sub_account_group(parent=another_account)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/groups/%s/" % group.pk, data={
            'name': 'Group Name',
            'children': [subaccount.pk],
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_update_subaccount_group_duplicate_name(api_client, user,
        create_sub_account, create_account, create_budget,
        create_sub_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(parent=account, budget=budget)
    create_sub_account_group(parent=account, name="Group Name")
    group = create_sub_account_group(parent=account)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/groups/%s/" % group.pk, data={
            'name': 'Group Name',
            'children': [subaccount.pk]
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_group_subaccount_already_in_group(api_client, user,
        create_sub_account, create_account, create_budget,
        create_sub_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    group = create_sub_account_group(parent=account)
    subaccount = create_sub_account(parent=account, budget=budget, group=group)

    another_group = create_sub_account_group(parent=account, name="Group Name")

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/groups/%s/" % another_group.pk, data={
            'name': 'Group Name',
            'children': [subaccount.pk]
        })
    assert response.status_code == 200
    subaccount.refresh_from_db()
    assert subaccount.group == another_group
    group.refresh_from_db()
    assert group.children.count() == 0


@pytest.mark.freeze_time('2020-01-01')
def test_delete_subaccount_group(api_client, user, create_account,
        create_budget, create_sub_account_group):
    budget = create_budget()
    account = create_account(budget=budget)
    group = create_sub_account_group(parent=account)

    api_client.force_login(user)
    response = api_client.delete(
        "/v1/subaccounts/groups/%s/" % group.pk)
    assert response.status_code == 204

    assert SubAccountGroup.objects.count() == 0
