import pytest

from greenbudget.app import signals


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_subaccount_subaccount_groups(api_client, user,
        create_budget_subaccount, create_budget_account, create_budget,
        create_budget_subaccount_group):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(budget=budget)
        subaccount = create_budget_subaccount(parent=account, budget=budget)
        group = create_budget_subaccount_group(parent=subaccount)
        child_subaccount = create_budget_subaccount(
            parent=subaccount,
            budget=budget,
            group=group
        )
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/groups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
        "id": group.pk,
        "name": group.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": group.color,
        "updated_by": user.pk,
        "actual": 0.0,
        "variance": 0.0,
        "estimated": 0.0,
        "created_by": user.pk,
        "children": [child_subaccount.pk]
    }]


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_subaccount_subaccount_groups(api_client, user,
        create_template_subaccount, create_template_account, create_template,
        create_template_subaccount_group):
    with signals.disable():
        template = create_template()
        account = create_template_account(budget=template)
        subaccount = create_template_subaccount(parent=account, budget=template)
        group = create_template_subaccount_group(parent=subaccount)
        child_subaccount = create_template_subaccount(
            parent=subaccount,
            budget=template,
            group=group
        )
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/groups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
        "id": group.pk,
        "name": group.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": group.color,
        "updated_by": user.pk,
        "estimated": 0.0,
        "created_by": user.pk,
        "children": [child_subaccount.pk]
    }]


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_subaccount_subaccount_group(api_client, user,
        create_budget_subaccount, create_budget_account, create_budget,
        models):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(budget=budget)
        subaccount = create_budget_subaccount(parent=account, budget=budget)
        child_subaccount = create_budget_subaccount(
            parent=subaccount,
            budget=budget
        )
    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/groups/" % subaccount.pk, data={
            'name': 'Group Name',
            'children': [child_subaccount.pk],
            'color': '#a1887f'
        })
    assert response.status_code == 201

    group = models.BudgetSubAccountGroup.objects.first()
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
        "updated_by": user.pk,
        "actual": 0.0,
        "variance": 0.0,
        "estimated": 0.0,
        "created_by": user.pk,
        "children": [child_subaccount.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_subaccount_subaccount_group(api_client, user,
        create_template_subaccount, create_template_account, create_template,
        models):
    with signals.disable():
        template = create_template()
        account = create_template_account(budget=template)
        subaccount = create_template_subaccount(parent=account, budget=template)
        child_subaccount = create_template_subaccount(
            parent=subaccount,
            budget=template
        )
    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/groups/" % subaccount.pk, data={
            'name': 'Group Name',
            'children': [child_subaccount.pk],
            'color': '#a1887f'
        })
    assert response.status_code == 201

    group = models.TemplateSubAccountGroup.objects.first()
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
        "updated_by": user.pk,
        "estimated": 0.0,
        "created_by": user.pk,
        "children": [child_subaccount.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_subaccount_subaccount_group_invalid_child(api_client,
        user, create_budget_subaccount, create_budget_account, create_budget):
    with signals.disable():
        budget = create_budget()
        account = create_budget_account(budget=budget)
        subaccount = create_budget_subaccount(parent=account, budget=budget)

        # We are trying to create the grouping under `another_sub_account` but
        # including children that belong to `child_subaccount`, which should
        # trigger a 400 response.
        another_sub_account = create_budget_subaccount(
            parent=account, budget=budget)
        child_subaccount = create_budget_subaccount(
            parent=subaccount, budget=budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/groups/" % another_sub_account.pk, data={
            'name': 'Group Name',
            'children': [child_subaccount.pk],
            'color': '#a1887f',
        })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_subaccount_subaccount_group_invalid_child(api_client,
        user, create_template_subaccount, create_template_account,
        create_template):
    with signals.disable():
        template = create_template()
        account = create_template_account(budget=template)
        subaccount = create_template_subaccount(parent=account, budget=template)

        # We are trying to create the grouping under `another_sub_account` but
        # including children that belong to `child_subaccount`, which should
        # trigger a 400 response.
        another_sub_account = create_template_subaccount(
            parent=account, budget=template)
        child_subaccount = create_template_subaccount(
            parent=subaccount, budget=template)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/groups/" % another_sub_account.pk, data={
            'name': 'Group Name',
            'children': [child_subaccount.pk],
            'color': '#a1887f',
        })
    assert response.status_code == 400
