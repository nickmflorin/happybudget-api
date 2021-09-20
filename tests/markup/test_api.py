import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_account_markup(api_client, user, create_budget_account,
        create_budget, create_budget_account_markup, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    markup = create_budget_account_markup(parent=budget, children=[account])

    api_client.force_login(user)
    response = api_client.get("/v1/markups/%s/" % markup.pk)

    assert response.status_code == 200
    assert response.json() == {
        "id": markup.pk,
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
        "children": [account.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_subaccount_markup(api_client, user, create_budget_account,
        create_budget, create_budget_subaccount_markup, models,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account)
    markup = create_budget_subaccount_markup(
        parent=account, children=[subaccount])

    api_client.force_login(user)
    response = api_client.get("/v1/markups/%s/" % markup.pk)

    assert response.status_code == 200
    assert response.json() == {
        "id": markup.pk,
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
        "children": [subaccount.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget_account_markup(api_client, user, create_budget_account,
        create_budget, create_budget_account_markup, models):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    markup = create_budget_account_markup(parent=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [account.pk],
    })
    assert response.status_code == 200

    markup.refresh_from_db()
    assert markup.identifier == "Markup Identifier"
    assert markup.children.count() == 1
    assert markup.children.first() == account
    assert markup.parent == budget

    assert response.json() == {
        "id": markup.pk,
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
        "children": [account.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget_subaccount_markup(api_client, user, create_budget_account,
        create_budget, create_budget_subaccount_markup, models,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=account)
    markup = create_budget_subaccount_markup(parent=account)

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
        "children": [subaccount.pk]
    }


def test_update_budget_account_markup_child_not_same_parent(api_client, user,
        create_budget_account, create_budget, create_budget_subaccount_markup):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(budget=another_budget)
    markup = create_budget_subaccount_markup(parent=budget)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [account.pk],
    })
    assert response.status_code == 400


def test_update_budget_subaccount_markup_not_same_parent(api_client, user,
        create_budget_account, create_budget, create_budget_subaccount_markup,
        create_budget_subaccount):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    another_account = create_budget_account(budget=budget)
    subaccount = create_budget_subaccount(parent=another_account)
    markup = create_budget_subaccount_markup(parent=account)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [subaccount.pk],
    })
    assert response.status_code == 400


def test_remove_budget_account_markup_child(api_client, user, models,
        create_budget_account, create_budget, create_budget_account_markup):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(budget=another_budget)
    markup = create_budget_account_markup(parent=budget, children=[account])

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/" % markup.pk,
        # If not specified, children will be excluded from payload.
        format='json',
        data={'children': []}
    )
    assert response.status_code == 200
    assert models.BudgetAccountMarkup.objects.count() == 0


def test_remove_budget_subaccount_markup_child(api_client, user, models,
        create_budget_account, create_budget, create_budget_subaccount_markup,
        create_budget_subaccount):
    budget = create_budget()
    another_budget = create_budget()
    account = create_budget_account(budget=another_budget)
    subaccount = create_budget_subaccount(parent=account)
    markup = create_budget_subaccount_markup(
        parent=budget, children=[subaccount])

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/" % markup.pk,
        # If not specified, children will be excluded from payload.
        format='json',
        data={'children': []}
    )
    assert response.status_code == 200
    assert models.BudgetSubAccountMarkup.objects.count() == 0


def test_delete_budget_account_markup(api_client, user, create_budget, models,
        create_budget_account_markup):
    budget = create_budget()
    markup = create_budget_account_markup(parent=budget)

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markup.pk)
    assert response.status_code == 204
    assert models.BudgetAccountMarkup.objects.count() == 0


def test_delete_budget_subaccount_markup(api_client, user, create_budget,
        models, create_budget_account, create_budget_subaccount_markup):
    budget = create_budget()
    account = create_budget_account(budget=budget)
    markup = create_budget_subaccount_markup(parent=account)

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markup.pk)
    assert response.status_code == 204
    assert models.BudgetSubAccountMarkup.objects.count() == 0
