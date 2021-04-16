import pytest

from greenbudget.app.group.models import (
    BudgetSubAccountGroup, TemplateSubAccountGroup)


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_account_subaccount_group(api_client, user,
        create_budget_subaccount, create_budget_account, create_budget):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)

    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/groups/" % account.pk, data={
        'name': 'Group Name',
        'children': [subaccount.pk],
        'color': '#a1887f',
    })
    assert response.status_code == 201

    group = BudgetSubAccountGroup.objects.first()
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
        "created_by": user.pk,
        "children": [subaccount.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_account_subaccount_group(api_client, user,
        create_template_subaccount, create_template_account, create_template):
    template = create_template()
    account = create_template_account(budget=template)
    subaccount = create_template_subaccount(parent=account, budget=template)

    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/groups/" % account.pk, data={
        'name': 'Group Name',
        'children': [subaccount.pk],
        'color': '#a1887f',
    })
    assert response.status_code == 201

    group = TemplateSubAccountGroup.objects.first()
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
        "estimated": None,
        "created_by": user.pk,
        "children": [subaccount.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_account_subaccount_group_duplicate_name(api_client, user,
        create_budget_subaccount, create_budget_account, create_budget,
        create_budget_subaccount_group):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account, budget=budget)
    create_budget_subaccount_group(name="Group Name", parent=account)

    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/groups/" % subaccount.pk, data={
        'name': 'Group Name',
        'children': [subaccount.pk]
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_account_subaccount_group_duplicate_name(api_client,
        user, create_template_subaccount, create_template_account,
        create_template, create_template_subaccount_group):
    template = create_template()
    account = create_template_account(budget=template)
    subaccount = create_template_subaccount(parent=account, budget=template)
    create_template_subaccount_group(name="Group Name", parent=account)

    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/groups/" % subaccount.pk, data={
        'name': 'Group Name',
        'children': [subaccount.pk]
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_account_subaccount_group_invalid_child(api_client, user,
        create_budget_subaccount, create_budget_account, create_budget):
    budget = create_budget()
    # We are trying to create the grouping under `account` but
    # including children that belong to `another_account`, which should
    # trigger a 400 response.
    account = create_budget_account(budget=budget)
    another_account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=another_account, budget=budget)

    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/groups/" % account.pk, data={
        'name': 'Group Name',
        'children': [subaccount.pk],
        'color': '#a1887f',
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_account_subaccount_group_invalid_child(api_client,
        user, create_template_subaccount, create_template_account,
        create_template):
    template = create_template()
    # We are trying to create the grouping under `account` but
    # including children that belong to `another_account`, which should
    # trigger a 400 response.
    account = create_template_account(budget=template)
    another_account = create_template_account(budget=template)
    subaccount = create_template_subaccount(
        parent=another_account,
        budget=template
    )
    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/groups/" % account.pk, data={
        'name': 'Group Name',
        'children': [subaccount.pk],
        'color': '#a1887f',
    })
    assert response.status_code == 400
