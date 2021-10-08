import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_account_markup(api_client, user, create_template_account,
        create_template, create_markup, models):
    template = create_template()
    account = create_template_account(parent=template)
    markup = create_markup(parent=template, accounts=[account])

    api_client.force_login(user)
    response = api_client.get("/v1/markups/%s/" % markup.pk)

    assert response.status_code == 200
    assert response.json() == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "actual": 0.0,
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
def test_get_template_subaccount_markup(api_client, user, create_template,
        create_template_account, create_markup, models,
        create_template_subaccount):
    template = create_template()
    account = create_template_account(parent=template)
    subaccount = create_template_subaccount(parent=account)
    markup = create_markup(parent=account, subaccounts=[subaccount])

    api_client.force_login(user)
    response = api_client.get("/v1/markups/%s/" % markup.pk)

    assert response.status_code == 200
    assert response.json() == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "actual": 0.0,
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
def test_update_template_account_markup_children(api_client, user, create_markup,
        create_template, create_template_account, models,
        create_template_subaccounts):
    template = create_template()
    markups = [
        create_markup(parent=template, flat=True, rate=20),
        create_markup(parent=template, flat=True, rate=30)
    ]
    accounts = [
        create_template_account(parent=template, markups=[markups[0]]),
        create_template_account(parent=template, markups=[markups[1]])
    ]
    create_template_subaccounts(parent=accounts[0], quantity=1, rate=10, count=2)
    create_template_subaccounts(parent=accounts[1], quantity=1, rate=10, count=2)

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 20.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 30.0

    template.refresh_from_db()
    assert template.nominal_value == 40.0
    assert template.accumulated_markup_contribution == 50.0

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markups[0].pk, data={
        'identifier': 'Markup Identifier',
        'children': [a.pk for a in accounts],
    })
    assert response.status_code == 200

    # We added the second account to the Markup children, so now the second
    # Account will have contributions from both Markups.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 20.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 50.0

    template.refresh_from_db()
    assert template.nominal_value == 40.0
    assert template.accumulated_markup_contribution == 70.0

    markups[0].refresh_from_db()
    assert markups[0].identifier == "Markup Identifier"
    assert markups[0].children.count() == 2

    assert response.json()["data"] == {
        "id": markups[0].pk,
        "type": "markup",
        "identifier": markups[0].identifier,
        "description": markups[0].description,
        "rate": markups[0].rate,
        "actual": 0.0,
        "unit": {
            "id": markups[0].unit,
            "name": models.Markup.UNITS[markups[0].unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [a.pk for a in accounts],
    }

    assert response.json()["budget"]["accumulated_markup_contribution"] == 70.0
    assert response.json()["budget"]["nominal_value"] == 40.0


@pytest.mark.freeze_time('2020-01-01')
def test_update_template_account_markup_rate(api_client, user, create_template,
        create_template_account, create_markup, models,
        create_template_subaccounts):
    template = create_template()
    markups = [
        create_markup(parent=template, flat=True, rate=20),
        create_markup(parent=template, flat=True, rate=30)
    ]
    accounts = [
        create_template_account(parent=template, markups=[markups[0]]),
        create_template_account(parent=template, markups=[markups[1]])
    ]
    create_template_subaccounts(parent=accounts[0], quantity=1, rate=10, count=2)
    create_template_subaccounts(parent=accounts[1], quantity=1, rate=10, count=2)

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 20.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 30.0

    template.refresh_from_db()
    assert template.nominal_value == 40.0
    assert template.accumulated_markup_contribution == 50.0

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markups[0].pk, data={
        'rate': 40.0,
    })
    assert response.status_code == 200

    # We increased the Markup rate for the first Markup - which belongs to the
    # first Account, so that Account should have it's Markup contributions
    # changed.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 40.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 30.0

    template.refresh_from_db()
    assert template.nominal_value == 40.0
    assert template.accumulated_markup_contribution == 70.0

    markups[0].refresh_from_db()
    assert markups[0].rate == 40.0

    assert response.json()["data"] == {
        "id": markups[0].pk,
        "type": "markup",
        "identifier": markups[0].identifier,
        "description": markups[0].description,
        "rate": markups[0].rate,
        "actual": 0.0,
        "unit": {
            "id": markups[0].unit,
            "name": models.Markup.UNITS[markups[0].unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [accounts[0].pk],
    }

    assert response.json()["budget"]["accumulated_markup_contribution"] == 70.0
    assert response.json()["budget"]["nominal_value"] == 40.0


@pytest.mark.freeze_time('2020-01-01')
def test_remove_template_account_markup_children(api_client, user, create_markup,
        create_template_account, create_template, create_template_subaccounts,
        models):
    template = create_template()
    account = create_template_account(parent=template)
    create_template_subaccounts(parent=account, quantity=1, rate=10, count=2)
    markup = create_markup(
        parent=template,
        flat=True,
        rate=20,
        accounts=[account]
    )

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 20.0

    template.refresh_from_db()
    assert template.nominal_value == 20.0
    assert template.accumulated_markup_contribution == 20.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/remove-children/" % markup.pk,
        data={'children': [account.pk]}
    )
    assert response.status_code == 200

    # The markup should be deleted because it does not have any children.
    with pytest.raises(models.Markup.DoesNotExist):
        markup.refresh_from_db()

    account.refresh_from_db()
    assert account.markup_contribution == 0.0

    template.refresh_from_db()
    assert template.accumulated_markup_contribution == 0.0

    assert response.json()["data"] == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "actual": 0.0,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [],
    }

    assert response.json()["budget"]["accumulated_markup_contribution"] == 0.0
    assert response.json()["budget"]["nominal_value"] == 20.0


@pytest.mark.freeze_time('2020-01-01')
def test_add_template_account_markup_children(api_client, user, create_markup,
        create_template_account, create_template, create_template_subaccounts,
        models):
    template = create_template()
    account = create_template_account(parent=template)
    create_template_subaccounts(parent=account, quantity=1, rate=10, count=2)
    markup = create_markup(parent=template, flat=True, rate=20)

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0

    template.refresh_from_db()
    assert template.nominal_value == 20.0
    assert template.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/add-children/" % markup.pk,
        data={'children': [account.pk]}
    )
    assert response.status_code == 200

    markup.refresh_from_db()
    assert markup.children.count() == 1

    account.refresh_from_db()
    assert account.markup_contribution == 20.0

    template.refresh_from_db()
    assert template.accumulated_markup_contribution == 20.0

    assert response.json()["data"] == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "actual": 0.0,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [account.pk],
    }

    assert response.json()["budget"]["accumulated_markup_contribution"] == 20.0
    assert response.json()["budget"]["nominal_value"] == 20.0


@pytest.mark.freeze_time('2020-01-01')
def test_update_template_subaccount_markup(api_client, user, create_template,
        create_template_account, create_markup, models,
        create_template_subaccounts):
    template = create_template()
    account = create_template_account(parent=template)
    subaccounts = create_template_subaccounts(
        parent=account,
        quantity=1,
        rate=10,
        count=2
    )
    markup = create_markup(parent=account, flat=True, rate=20)

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0

    template.refresh_from_db()
    assert template.nominal_value == 20.0
    assert template.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [s.pk for s in subaccounts],
    })
    assert response.status_code == 200

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 20.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 20.0

    account.refresh_from_db()
    assert account.accumulated_markup_contribution == 40.0

    template.refresh_from_db()
    assert template.accumulated_markup_contribution == 40.0

    markup.refresh_from_db()
    assert markup.identifier == "Markup Identifier"
    assert markup.children.count() == 2
    assert markup.children.all()[0] == subaccounts[0]
    assert markup.children.all()[1] == subaccounts[1]
    assert markup.parent == account

    assert response.json()["data"] == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "actual": 0.0,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [s.pk for s in subaccounts],
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 40.0
    assert response.json()["parent"]["nominal_value"] == 20.0

    assert response.json()["budget"]["accumulated_markup_contribution"] == 40.0
    assert response.json()["budget"]["nominal_value"] == 20.0


@pytest.mark.freeze_time('2020-01-01')
def test_remove_template_subaccount_markup_children(api_client, user, models,
        create_template_account, create_template, create_template_subaccounts,
        create_markup):
    template = create_template()
    account = create_template_account(parent=template)
    subaccounts = create_template_subaccounts(
        parent=account,
        quantity=1,
        rate=10,
        count=2
    )
    markup = create_markup(
        parent=account,
        flat=True,
        rate=20,
        subaccounts=subaccounts
    )

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 20.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 20.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.accumulated_markup_contribution == 40.0

    template.refresh_from_db()
    assert template.nominal_value == 20.0
    assert template.accumulated_markup_contribution == 40.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/remove-children/" % markup.pk,
        data={'children': [s.pk for s in subaccounts]}
    )
    assert response.status_code == 200

    # The markup should be deleted because it does not have any children.
    with pytest.raises(models.Markup.DoesNotExist):
        markup.refresh_from_db()

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0

    account.refresh_from_db()
    assert account.accumulated_markup_contribution == 0.0

    template.refresh_from_db()
    assert template.accumulated_markup_contribution == 0.0

    assert response.json()["data"] == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "actual": 0.0,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [],
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 0.0
    assert response.json()["parent"]["nominal_value"] == 20.0

    assert response.json()["budget"]["accumulated_markup_contribution"] == 0.0
    assert response.json()["budget"]["nominal_value"] == 20.0


@pytest.mark.freeze_time('2020-01-01')
def test_add_template_subaccount_markup_children(api_client, user, create_markup,
        create_template_account, create_template, create_template_subaccounts,
        models):
    template = create_template()
    account = create_template_account(parent=template)
    subaccounts = create_template_subaccounts(
        parent=account,
        quantity=1,
        rate=10,
        count=2
    )
    markup = create_markup(parent=account, flat=True, rate=20)

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.accumulated_markup_contribution == 0.0

    template.refresh_from_db()
    assert template.nominal_value == 20.0
    assert template.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/add-children/" % markup.pk,
        data={'children': [s.pk for s in subaccounts]}
    )
    assert response.status_code == 200

    markup.refresh_from_db()
    assert markup.children.count() == 2

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 20.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 20.0

    account.refresh_from_db()
    assert account.accumulated_markup_contribution == 40.0

    template.refresh_from_db()
    assert template.accumulated_markup_contribution == 40.0

    assert response.json()["data"] == {
        "id": markup.pk,
        "type": "markup",
        "identifier": markup.identifier,
        "description": markup.description,
        "rate": markup.rate,
        "actual": 0.0,
        "unit": {
            "id": markup.unit,
            "name": models.Markup.UNITS[markup.unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [s.pk for s in subaccounts],
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 40.0
    assert response.json()["parent"]["nominal_value"] == 20.0

    assert response.json()["budget"]["accumulated_markup_contribution"] == 40.0
    assert response.json()["budget"]["nominal_value"] == 20.0


def test_update_template_account_markup_child_not_same_parent(api_client, user,
        create_template_account, create_template, create_markup):
    template = create_template()
    another_template = create_template()
    account = create_template_account(parent=another_template)
    markup = create_markup(parent=template)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [account.pk],
    })
    assert response.status_code == 400


def test_update_template_subaccount_markup_child_not_same_parent(api_client,
        user, create_template_account, create_template, create_markup,
        create_template_subaccount):
    template = create_template()
    account = create_template_account(parent=template)
    another_account = create_template_account(parent=template)
    subaccount = create_template_subaccount(parent=another_account)
    markup = create_markup(parent=account)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [subaccount.pk],
    })
    assert response.status_code == 400


def test_delete_template_account_markup(api_client, user, create_template,
        models, create_markup):
    template = create_template()
    markup = create_markup(parent=template)

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markup.pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 0


def test_delete_template_subaccount_markup(api_client, user, create_template,
        models, create_template_account, create_markup):
    template = create_template()
    account = create_template_account(parent=template)
    markup = create_markup(parent=account)

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markup.pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 0
