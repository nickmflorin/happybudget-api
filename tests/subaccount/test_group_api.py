import pytest


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_get_subaccount_subaccount_groups(api_client, user, context,
        create_subaccount, create_account, create_context_budget, create_group):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    group = create_group(parent=subaccount)
    child_subaccount = create_subaccount(
        parent=subaccount,
        group=group,
        context=context
    )
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/groups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
        "id": group.pk,
        "type": "group",
        "name": group.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": group.color,
        "updated_by": user.pk,
        "created_by": user.pk,
        "children": [child_subaccount.pk]
    }]


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_create_subaccount_subaccount_group(api_client, user, create_account,
        create_subaccount, models, create_context_budget, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    child_subaccount = create_subaccount(parent=subaccount, context=context)

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
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": '#a1887f',
        "updated_by": user.pk,
        "created_by": user.pk,
        "children": [child_subaccount.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_create_subaccount_subaccount_group_invalid_child(api_client, context,
        user, create_subaccount, create_account, create_context_budget):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    # We are trying to create the grouping under `another_sub_account` but
    # including children that belong to `child_subaccount`, which should
    # trigger a 400 response.
    another_sub_account = create_subaccount(parent=account, context=context)
    child_subaccount = create_subaccount(parent=subaccount, context=context)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/groups/" % another_sub_account.pk, data={
            'name': 'Group Name',
            'children': [child_subaccount.pk],
            'color': '#a1887f',
        })
    assert response.status_code == 400
