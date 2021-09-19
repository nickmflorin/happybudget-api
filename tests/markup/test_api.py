import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_account_markup(api_client, user, create_budget_account,
        create_budget, create_markup, create_group, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    groups = [
        create_group(parent=budget),
        create_group(parent=budget)
    ]
    markup = create_markup(parent=budget, accounts=[account], groups=groups)

    api_client.force_login(user)
    response = api_client.get("/v1/markups/%s/" % markup.pk)

    assert response.status_code == 200
    assert response.json() == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [account.pk],
        'groups': [g.pk for g in groups]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_subaccount_markup(api_client, user, create_budget_account,
        create_budget, create_markup, models, create_group,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)
    groups = [
        create_group(parent=account),
        create_group(parent=account)
    ]
    markup = create_markup(
        parent=account,
        subaccounts=[subaccount],
        groups=groups
    )

    api_client.force_login(user)
    response = api_client.get("/v1/markups/%s/" % markup.pk)

    assert response.status_code == 200
    assert response.json() == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [subaccount.pk],
        'groups': [g.pk for g in groups]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget_account_markup(api_client, user, create_budget_account,
        create_budget, create_markup, models, create_group):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    groups = [
        create_group(parent=budget),
        create_group(parent=budget)
    ]
    markup = create_markup(parent=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [account.pk],
        'groups': [g.pk for g in groups]
    })
    assert response.status_code == 200

    markup.refresh_from_db()
    assert markup.identifier == "Markup Identifier"
    assert markup.children.count() == 1
    assert markup.children.first() == account
    assert markup.groups.count() == 2
    assert [g.pk for g in markup.groups.all()] == [g.pk for g in groups]
    assert markup.parent == budget

    assert response.json() == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [account.pk],
        'groups': [g.pk for g in groups]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_remove_budget_account_markup_children(api_client, user, create_group,
        create_budget_account, create_budget, create_markup, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    group = create_group(parent=budget)
    markup = create_markup(parent=budget, accounts=[account], groups=[group])

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/remove-children/" % markup.pk,
        data={'children': [account.pk], 'groups': [group.pk]}
    )
    assert response.status_code == 200

    # The markup should be deleted because it does not have any children.
    with pytest.raises(models.Markup.DoesNotExist):
        markup.refresh_from_db()

    assert response.json() == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [],
        "groups": []
    }


@pytest.mark.freeze_time('2020-01-01')
def test_add_budget_account_markup_children(api_client, user, create_group,
        create_budget_account, create_budget, create_markup, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    group = create_group(parent=budget)
    markup = create_markup(parent=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/add-children/" % markup.pk,
        data={'children': [account.pk], 'groups': [group.pk]}
    )
    assert response.status_code == 200

    markup.refresh_from_db()
    assert markup.children.count() == 1
    assert markup.groups.count() == 1

    assert response.json() == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [account.pk],
        "groups": [group.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget_subaccount_markup(api_client, user, create_budget_account,
        create_budget, create_markup, models,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)
    markup = create_markup(parent=account)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [subaccount.pk],
    })

    assert response.status_code == 200

    markup.refresh_from_db()
    assert markup.identifier == "Markup Identifier"
    assert markup.children.count() == 1
    assert markup.children.first() == subaccount
    assert markup.parent == account

    assert response.json() == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [subaccount.pk],
        "groups": []
    }


@pytest.mark.freeze_time('2020-01-01')
def test_remove_budget_subaccount_markup_children(api_client, user, models,
        create_budget_account, create_budget, create_markup, create_group,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)
    group = create_group(parent=account)
    markup = create_markup(
        parent=account,
        subaccounts=[subaccount],
        groups=[group]
    )

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/remove-children/" % markup.pk,
        data={'children': [subaccount.pk], 'groups': [group.pk]}
    )

    assert response.status_code == 200
    assert models.Markup.objects.count() == 0

    assert response.json() == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [],
        "groups": []
    }


@pytest.mark.freeze_time('2020-01-01')
def test_add_budget_subaccount_markup_children(api_client, user, create_group,
        create_budget_account, create_budget, create_markup, models,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)
    group = create_group(parent=account)
    markup = create_markup(parent=account)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/add-children/" % markup.pk,
        format='json',
        data={'children': [subaccount.pk], 'groups': [group.pk]}
    )
    assert response.status_code == 200

    markup.refresh_from_db()
    assert markup.children.count() == 1
    assert markup.groups.count() == 1

    assert response.json() == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [subaccount.pk],
        "groups": [group.pk]
    }


def test_update_budget_account_markup_child_not_same_parent(api_client, user,
        create_budget_account, create_budget, create_markup):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(parent=another_budget)
    markup = create_markup(parent=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [account.pk],
    })
    assert response.status_code == 400


def test_update_budget_account_markup_group_not_same_parent(api_client, user,
        create_budget, create_markup, create_group):
    budget = create_budget()
    another_budget = create_budget()
    group = create_group(parent=another_budget)
    markup = create_markup(parent=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'groups': [group.pk],
    })
    assert response.status_code == 400


def test_update_budget_subaccount_markup_child_not_same_parent(api_client, user,
        create_budget_account, create_budget, create_markup,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    another_account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=another_account)
    markup = create_markup(parent=account)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [subaccount.pk],
    })
    assert response.status_code == 400


def test_update_budget_subaccount_markup_group_not_same_parent(api_client, user,
        create_budget_account, create_budget, create_markup,
        create_group):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    another_account = create_budget_account(parent=budget)
    group = create_group(parent=another_account)
    markup = create_markup(parent=account)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'groups': [group.pk],
    })
    assert response.status_code == 400


def test_remove_budget_account_markup_child(api_client, user, models,
        create_budget_account, create_budget, create_markup):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    markup = create_markup(parent=budget, accounts=[account])

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/" % markup.pk,
        # If not specified, children will be excluded from payload.
        format='json',
        data={'children': []}
    )
    assert response.status_code == 200
    assert models.Markup.objects.count() == 0


def test_remove_budget_account_markup_group(api_client, user, models,
        create_group, create_budget, create_markup):
    budget = create_budget()
    group = create_group(parent=budget)
    markup = create_markup(parent=budget, groups=[group])

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/" % markup.pk,
        # If not specified, children will be excluded from payload.
        format='json',
        data={'groups': []}
    )
    assert response.status_code == 200
    assert models.Markup.objects.count() == 0


def test_remove_budget_subaccount_markup_child(api_client, user, models,
        create_budget_account, create_budget, create_markup,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)
    markup = create_markup(parent=account, subaccounts=[subaccount])

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/" % markup.pk,
        # If not specified, children will be excluded from payload.
        format='json',
        data={'children': []}
    )
    assert response.status_code == 200
    assert models.Markup.objects.count() == 0


def test_remove_budget_subaccount_markup_group(api_client, user, models,
        create_budget_account, create_budget, create_markup, create_group):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    group = create_group(parent=account)
    markup = create_markup(parent=account, groups=[group])

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/" % markup.pk,
        # If not specified, children will be excluded from payload.
        format='json',
        data={'groups': []}
    )
    assert response.status_code == 200
    assert models.Markup.objects.count() == 0


def test_delete_budget_account_markup(api_client, user, create_budget, models,
        create_markup):
    budget = create_budget()
    markup = create_markup(parent=budget)

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markup.pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 0


def test_delete_budget_subaccount_markup(api_client, user, create_budget,
        models, create_budget_account, create_markup):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    markup = create_markup(parent=account)

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markup.pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 0
