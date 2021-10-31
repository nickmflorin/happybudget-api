import pytest


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_get_budget_account_subaccount_groups(api_client, user, create_group,
        create_subaccount, create_account, create_context_budget, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    group = create_group(parent=account)
    subaccount = create_subaccount(
        parent=account,
        group=group,
        context=context
    )
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
        "id": group.pk,
        "name": group.name,
        "type": "group",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": group.color,
        "updated_by": user.pk,
        "created_by": user.pk,
        "children": [subaccount.pk]
    }]


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_create_account_subaccount_group(api_client, user, create_subaccount,
        create_context_budget, create_account, models, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)

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
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "updated_by": user.pk,
        "color": '#a1887f',
        "created_by": user.pk,
        "children": [subaccount.pk]
    }


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_create_account_subaccount_group_invalid_child(api_client, user,
        create_subaccount, create_account, create_context_budget, context):
    budget = create_context_budget(context=context)
    # We are trying to create the grouping under `account` but
    # including children that belong to `another_account`, which should
    # trigger a 400 response.
    account = create_account(parent=budget, context=context)
    another_account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=another_account, context=context)

    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/groups/" % account.pk, data={
        'name': 'Group Name',
        'children': [subaccount.pk],
        'color': '#a1887f',
    })
    assert response.status_code == 400
