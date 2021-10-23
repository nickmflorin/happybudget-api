import pytest


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_get_account_markup(api_client, user, create_account, context,
        create_context_budget, create_markup, models):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    markup = create_markup(parent=budget, accounts=[account])

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
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_get_subaccount_markup(api_client, user, create_account, context,
        create_context_budget, create_markup, models, create_subaccount):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
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
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_markup_children(api_client, user, create_context_budget,
        create_markup, create_account, models, create_subaccounts, context):
    budget = create_context_budget(context=context)
    markups = [
        create_markup(parent=budget, flat=True, rate=20),
        create_markup(parent=budget, flat=True, rate=30),
        create_markup(parent=budget, percent=True, rate=0.5)
    ]
    accounts = [
        create_account(parent=budget, markups=[markups[2]], context=context),
        create_account(parent=budget, markups=[markups[2]], context=context),
        create_account(parent=budget, markups=[markups[2]], context=context)
    ]
    subaccount_sets = [
        create_subaccounts(
            parent=accounts[0],
            quantity=1,
            rate=10,
            count=2,
            context=context
        ),
        create_subaccounts(
            parent=accounts[1],
            quantity=1,
            rate=10,
            count=2,
            context=context
        ),
        create_subaccounts(
            parent=accounts[2],
            quantity=1,
            rate=10,
            count=2,
            context=context
        ),
    ]
    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    for subaccounts in subaccount_sets:
        for i, sub in enumerate(subaccounts):
            assert sub.nominal_value == 10.0, \
                "Sub Account %s has incorrect nominal_value." % i
            assert sub.markup_contribution == 0, \
                "Sub Account %s has incorrect markup_contribution." % i

    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 10.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 10.0

    accounts[2].refresh_from_db()
    assert accounts[2].nominal_value == 20.0
    assert accounts[2].markup_contribution == 10.0

    budget.refresh_from_db()
    assert budget.nominal_value == 60.0
    assert budget.accumulated_markup_contribution == 80.0

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markups[0].pk, data={
        'identifier': 'Markup Identifier',
        'unit': models.Markup.UNITS.percent,
        'rate': 0.5,
        'children': [a.pk for a in accounts],
    })
    assert response.status_code == 200

    for subaccounts in subaccount_sets:
        for i, sub in enumerate(subaccounts):
            assert sub.nominal_value == 10.0, \
                "Sub Account %s has incorrect nominal_value." % i
            assert sub.markup_contribution == 0, \
                "Sub Account %s has incorrect markup_contribution." % i

    # We added the second account to the Markup children, so now the second
    # Account will have contributions from both Markups.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 20.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 20.0

    accounts[2].refresh_from_db()
    assert accounts[2].nominal_value == 20.0
    assert accounts[2].markup_contribution == 20.0

    budget.refresh_from_db()
    assert budget.nominal_value == 60.0
    assert budget.accumulated_markup_contribution == 90.0

    markups[0].refresh_from_db()
    assert markups[0].identifier == "Markup Identifier"
    assert markups[0].children.count() == 3

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

    assert response.json()["budget"]["accumulated_markup_contribution"] == 90.0
    assert response.json()["budget"]["nominal_value"] == 60.0


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_account_markup_children(api_client, user, create_context_budget,
        create_markup, create_account, models, create_subaccount, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    markups = [
        create_markup(parent=account, flat=True, rate=20),
        create_markup(parent=account, percent=True, rate=0.5),
        create_markup(parent=account, percent=True, rate=0.5)
    ]
    subaccounts = [
        create_subaccount(
            parent=account,
            quantity=1,
            rate=10,
            markups=[markups[1]],
            context=context
        ),
        create_subaccount(
            parent=account,
            quantity=1,
            rate=10,
            markups=[markups[2]],
            context=context
        )
    ]

    for i, sub in enumerate(subaccounts):
        assert sub.nominal_value == 10.0, \
            "Sub Account %s has incorrect nominal_value." % i
        assert sub.markup_contribution == 5.0, \
            "Sub Account %s has incorrect markup_contribution." % i

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 30.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 30.0

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markups[1].pk, data={
        'identifier': 'Markup Identifier',
        'unit': models.Markup.UNITS.percent,
        'rate': 0.5,
        'children': [a.pk for a in subaccounts],
    })
    assert response.status_code == 200

    for i, sub in enumerate(subaccounts):
        sub.refresh_from_db()
        assert sub.nominal_value == 10.0, \
            "Sub Account %s has incorrect nominal_value." % i

    assert subaccounts[0].markup_contribution == 5.0
    assert subaccounts[1].markup_contribution == 10.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 35.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 35.0

    markups[1].refresh_from_db()
    assert markups[1].identifier == "Markup Identifier"
    assert markups[1].children.count() == 2

    assert response.json()["data"] == {
        "id": markups[1].pk,
        "type": "markup",
        "identifier": markups[1].identifier,
        "description": markups[1].description,
        "rate": markups[1].rate,
        "actual": 0.0,
        "unit": {
            "id": markups[1].unit,
            "name": models.Markup.UNITS[markups[1].unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [a.pk for a in subaccounts],
    }

    assert response.json()["budget"]["accumulated_markup_contribution"] == 35.0
    assert response.json()["budget"]["nominal_value"] == 20.0


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_subaccount_markup_children(api_client, user, context, models,
        create_context_budget, create_markup, create_account, create_subaccount):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    markups = [
        create_markup(parent=subaccount, flat=True, rate=20),
        create_markup(parent=subaccount, percent=True, rate=0.5),
        create_markup(parent=subaccount, percent=True, rate=0.5)
    ]
    children_subaccounts = [
        create_subaccount(
            parent=subaccount,
            quantity=1,
            rate=10,
            markups=[markups[1]],
            context=context
        ),
        create_subaccount(
            parent=subaccount,
            quantity=1,
            rate=10,
            markups=[markups[2]],
            context=context
        )
    ]

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    for i, sub in enumerate(children_subaccounts):
        sub.refresh_from_db()
        assert sub.nominal_value == 10.0, \
            "Sub Account %s has incorrect nominal_value." % i
        assert sub.markup_contribution == 5.0, \
            "Sub Account %s has incorrect markup_contribution." % i

    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 20.0
    assert subaccount.markup_contribution == 0.0
    assert subaccount.accumulated_markup_contribution == 30.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 30.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 30.0

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markups[1].pk, data={
        'identifier': 'Markup Identifier',
        'unit': models.Markup.UNITS.percent,
        'rate': 0.5,
        'children': [a.pk for a in children_subaccounts],
    })
    assert response.status_code == 200

    for i, sub in enumerate(children_subaccounts):
        sub.refresh_from_db()
        assert sub.nominal_value == 10.0, \
            "Sub Account %s has incorrect nominal_value." % i

    assert children_subaccounts[0].markup_contribution == 5.0
    assert children_subaccounts[1].markup_contribution == 10.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 35.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 35.0

    markups[1].refresh_from_db()
    assert markups[1].identifier == "Markup Identifier"
    assert markups[1].children.count() == 2

    assert response.json()["data"] == {
        "id": markups[1].pk,
        "type": "markup",
        "identifier": markups[1].identifier,
        "description": markups[1].description,
        "rate": markups[1].rate,
        "actual": 0.0,
        "unit": {
            "id": markups[1].unit,
            "name": models.Markup.UNITS[markups[1].unit]
        },
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "created_by": user.pk,
        "updated_by": user.pk,
        "children": [a.pk for a in children_subaccounts],
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 35.0
    assert response.json()["parent"]["nominal_value"] == 20.0

    assert response.json()["budget"]["accumulated_markup_contribution"] == 35.0
    assert response.json()["budget"]["nominal_value"] == 20.0


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_account_flat_markup_rate(api_client, user, create_context_budget,
        models, create_account, create_markup, create_subaccounts, context):
    budget = create_context_budget(context=context)
    markups = [
        create_markup(parent=budget, flat=True, rate=20),
        create_markup(parent=budget, flat=True, rate=30)
    ]
    accounts = [
        create_account(parent=budget, context=context),
        create_account(parent=budget, context=context)
    ]
    create_subaccounts(
        parent=accounts[0],
        quantity=1,
        rate=10,
        count=2,
        context=context
    )
    create_subaccounts(
        parent=accounts[1],
        quantity=1,
        rate=10,
        count=2,
        context=context
    )

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 0.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 40.0
    assert budget.accumulated_markup_contribution == 50.0

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markups[0].pk, data={
        'rate': 40.0,
    })
    assert response.status_code == 200

    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 0.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 40.0
    assert budget.accumulated_markup_contribution == 70.0

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
    }

    assert response.json()["budget"]["accumulated_markup_contribution"] == 70.0
    assert response.json()["budget"]["nominal_value"] == 40.0


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_change_account_flat_markup_to_percent(api_client, user, models,
        create_context_budget, create_account, create_markup, context,
        create_subaccounts):
    budget = create_context_budget(context=context)
    markups = [
        create_markup(parent=budget, flat=True, rate=20),
        create_markup(parent=budget, flat=True, rate=30)
    ]
    accounts = [
        create_account(parent=budget, context=context),
        create_account(parent=budget, context=context)
    ]
    create_subaccounts(
        context=context,
        parent=accounts[0],
        quantity=1,
        rate=10,
        count=2
    )
    create_subaccounts(
        context=context,
        parent=accounts[1],
        quantity=1,
        rate=10,
        count=2
    )
    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 0.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 40.0
    assert budget.accumulated_markup_contribution == 50.0

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markups[0].pk, data={
        'unit': models.Markup.UNITS.percent,
        'children': [accounts[1].pk],
        'rate': 0.5
    })
    assert response.status_code == 200

    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 0.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 10.0

    budget.refresh_from_db()
    assert budget.nominal_value == 40.0
    assert budget.accumulated_markup_contribution == 40.0

    markups[0].refresh_from_db()
    assert markups[0].rate == 0.5
    assert markups[0].unit == models.Markup.UNITS.percent
    assert markups[0].children.count() == 1

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
        "children": [accounts[1].pk]
    }

    assert response.json()["budget"]["accumulated_markup_contribution"] == 40.0
    assert response.json()["budget"]["nominal_value"] == 40.0


@pytest.mark.parametrize('context,data', [
    ('budget', {}),
    ('budget', {'children': []}),
    ('template', {}),
    ('template', {'children': []}),
])
def test_change_account_flat_markup_to_percent_no_children(api_client, user,
        models, create_context_budget, create_account, create_markup, context,
        create_subaccounts, data):
    budget = create_context_budget(context=context)
    markups = [
        create_markup(parent=budget, flat=True, rate=20),
        create_markup(parent=budget, flat=True, rate=30)
    ]
    accounts = [
        create_account(parent=budget, context=context),
        create_account(parent=budget, context=context)
    ]
    create_subaccounts(
        context=context,
        parent=accounts[0],
        quantity=1,
        rate=10,
        count=2
    )
    create_subaccounts(
        context=context,
        parent=accounts[1],
        quantity=1,
        rate=10,
        count=2
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markups[0].pk, data={
        **data,
        **{
            'unit': models.Markup.UNITS.percent,
            'rate': 0.5
        }
    })
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': 'A markup with unit `percent` must have at least 1 child.',  # noqa
            'code': 'invalid',
            'error_type': 'field',
            'field': 'children'
        }]
    }


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_account_percent_markup_rate(api_client, user, context, models,
        create_context_budget, create_account, create_markup,
        create_subaccounts):
    budget = create_context_budget(context=context)
    markups = [
        create_markup(parent=budget, percent=True, rate=0.5),
        create_markup(parent=budget, flat=True, rate=30)
    ]
    accounts = [
        create_account(parent=budget, markups=[markups[0]], context=context),
        create_account(parent=budget, markups=[markups[0]], context=context)
    ]
    create_subaccounts(
        parent=accounts[0],
        quantity=1,
        rate=10,
        count=2,
        context=context
    )
    create_subaccounts(
        parent=accounts[1],
        quantity=1,
        rate=10,
        count=2,
        context=context
    )
    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 10.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 10.0

    budget.refresh_from_db()
    assert budget.nominal_value == 40.0
    assert budget.accumulated_markup_contribution == 50.0

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markups[0].pk, data={
        'rate': 0.6
    })

    assert response.status_code == 200

    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 12.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 12.0

    budget.refresh_from_db()
    assert budget.nominal_value == 40.0
    assert budget.accumulated_markup_contribution == 54.0

    markups[0].refresh_from_db()
    assert markups[0].rate == 0.6

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

    assert response.json()["budget"]["accumulated_markup_contribution"] == 54.0
    assert response.json()["budget"]["nominal_value"] == 40.0


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_change_account_percent_markup_to_flat(api_client, user, models,
        create_context_budget, create_account, create_markup, create_subaccounts,
        context):
    budget = create_context_budget(context=context)
    markups = [
        create_markup(parent=budget, percent=True, rate=0.5),
        create_markup(parent=budget, flat=True, rate=30)
    ]
    accounts = [
        create_account(parent=budget, markups=[markups[0]], context=context),
        create_account(parent=budget, markups=[markups[0]], context=context)
    ]
    create_subaccounts(
        parent=accounts[0],
        quantity=1,
        rate=10,
        count=2,
        context=context
    )
    create_subaccounts(
        parent=accounts[1],
        quantity=1,
        rate=10,
        count=2,
        context=context
    )
    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 10.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 10.0

    budget.refresh_from_db()
    assert budget.nominal_value == 40.0
    assert budget.accumulated_markup_contribution == 50.0

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markups[0].pk, data={
        'rate': 20,
        'unit': models.Markup.UNITS.flat
    })

    assert response.status_code == 200

    accounts[0].refresh_from_db()
    assert accounts[0].markups.count() == 0
    assert accounts[0].nominal_value == 20.0
    assert accounts[0].markup_contribution == 0.0

    accounts[1].refresh_from_db()
    assert accounts[1].markups.count() == 0
    assert accounts[1].nominal_value == 20.0
    assert accounts[1].markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 40.0
    assert budget.accumulated_markup_contribution == 50.0

    markups[0].refresh_from_db()
    assert markups[0].rate == 20
    assert markups[0].unit == models.Markup.UNITS.flat
    assert markups[0].children.count() == 0

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
        "updated_by": user.pk
    }

    assert response.json()["budget"]["accumulated_markup_contribution"] == 50.0
    assert response.json()["budget"]["nominal_value"] == 40.0


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_change_account_percent_markup_to_flat_children(api_client, user, models,
        create_context_budget, create_account, create_markup, create_subaccounts,
        context):
    budget = create_context_budget(context=context)
    markups = [
        create_markup(parent=budget, percent=True, rate=0.5),
        create_markup(parent=budget, flat=True, rate=30)
    ]
    accounts = [
        create_account(parent=budget, markups=[markups[0]], context=context),
        create_account(parent=budget, markups=[markups[0]], context=context)
    ]
    another_account = create_account(parent=budget, context=context)
    create_subaccounts(
        parent=accounts[0],
        quantity=1,
        rate=10,
        count=2,
        context=context
    )
    create_subaccounts(
        parent=accounts[1],
        quantity=1,
        rate=10,
        count=2,
        context=context
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markups[0].pk, data={
        'rate': 20,
        'unit': models.Markup.UNITS.flat,
        'children': [another_account.pk]
    })
    assert response.json() == {
        'errors': [{
            'message': 'A markup with unit `flat` cannot have children.',
            'code': 'invalid',
            'error_type': 'field',
            'field': 'children'
        }]
    }


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_remove_account_flat_markup_children(api_client, user, create_markup,
        create_account, create_context_budget, create_subaccounts, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    create_subaccounts(
        parent=account,
        quantity=1,
        rate=10,
        count=2,
        context=context
    )
    markup = create_markup(parent=budget, flat=True, rate=20)
    api_client.force_login(user)
    # Note: This is kind of a dumb test, because we will not get the exception
    # indicating that we cannot remove the children due to the Markup being of
    # type FLAT because the child won't actually exist, because the DB prevents
    # us from doing that in the first place.
    response = api_client.patch(
        "/v1/markups/%s/remove-children/" % markup.pk,
        data={'children': [account.pk]}
    )
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_remove_percent_markup_children(api_client, user, create_markup,
        create_account, create_context_budget, create_subaccounts, models,
        context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    create_subaccounts(
        parent=account,
        quantity=1,
        context=context,
        rate=10,
        count=2
    )
    markup = create_markup(
        parent=budget,
        percent=True,
        rate=0.5,
        accounts=[account]
    )

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 10.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 10.0

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

    budget.refresh_from_db()
    assert budget.accumulated_markup_contribution == 0.0

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


@pytest.mark.skip("Need to write this test.")
def test_remove_account_percent_markup_children():
    pass


@pytest.mark.skip("Need to write this test.")
def test_remove_subaccount_percent_markup_children():
    pass


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_add_account_flat_markup_children(api_client, user, create_markup,
        create_account, create_context_budget, create_subaccounts, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    create_subaccounts(
        parent=account,
        quantity=1,
        rate=10,
        count=2,
        context=context
    )
    markup = create_markup(parent=budget, flat=True, rate=20)
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/add-children/" % markup.pk,
        data={'children': [account.pk]}
    )
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': 'Markup must have unit `percent` to modify its children.',  # noqa
            'code': 'invalid',
            'error_type': 'field',
            'field': 'children'
        }]
    }


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_add_percent_markup_children(api_client, user, create_markup, models,
        create_account, create_context_budget, create_subaccounts, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    create_subaccounts(
        parent=account,
        quantity=1,
        rate=10,
        count=2,
        context=context
    )
    markup = create_markup(parent=budget, percent=True, rate=0.50)

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/add-children/" % markup.pk,
        data={'children': [account.pk]}
    )
    assert response.status_code == 200

    markup.refresh_from_db()
    assert markup.children.count() == 1

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 10.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 10.0

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

    assert response.json()["budget"]["accumulated_markup_contribution"] == 10.0
    assert response.json()["budget"]["nominal_value"] == 20.0


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_add_account_percent_markup_children(api_client, user, create_markup,
        models, create_account, create_context_budget, create_subaccounts,
        context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    markup = create_markup(parent=account, percent=True, rate=0.50)
    subaccounts = create_subaccounts(
        parent=account,
        quantity=1,
        rate=10,
        count=2,
        context=context
    )

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0

    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/add-children/" % markup.pk,
        data={'children': [subaccounts[0].pk]}
    )
    assert response.status_code == 200

    markup.refresh_from_db()
    assert markup.children.count() == 1

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 5.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 5.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 5.0

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
        "children": [subaccounts[0].pk]
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 5.0
    assert response.json()["parent"]["nominal_value"] == 20.0

    assert response.json()["budget"]["accumulated_markup_contribution"] == 5.0
    assert response.json()["budget"]["nominal_value"] == 20.0


@pytest.mark.freeze_time('2020-01-01')
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_add_subaccount_percent_markup_children(api_client, user, create_markup,
        models, create_account, create_context_budget, create_subaccount,
        create_subaccounts, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    markup = create_markup(parent=subaccount, percent=True, rate=0.50)
    children_subaccounts = create_subaccounts(
        parent=subaccount,
        quantity=1,
        rate=10,
        count=2,
        context=context
    )
    # Make sure all data is properly calculated before API request to avoid
    # confusion in source of potential errors.
    children_subaccounts[0].refresh_from_db()
    assert children_subaccounts[0].nominal_value == 10.0
    assert children_subaccounts[0].markup_contribution == 0.0

    children_subaccounts[1].refresh_from_db()
    assert children_subaccounts[1].nominal_value == 10.0
    assert children_subaccounts[1].markup_contribution == 0.0

    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 20.0
    assert subaccount.markup_contribution == 0.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/markups/%s/add-children/" % markup.pk,
        data={'children': [children_subaccounts[0].pk]}
    )
    assert response.status_code == 200

    markup.refresh_from_db()
    assert markup.children.count() == 1

    children_subaccounts[0].refresh_from_db()
    assert children_subaccounts[0].nominal_value == 10.0
    assert children_subaccounts[0].markup_contribution == 5.0

    children_subaccounts[1].refresh_from_db()
    assert children_subaccounts[1].nominal_value == 10.0
    assert children_subaccounts[1].markup_contribution == 0.0

    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 20.0
    assert subaccount.markup_contribution == 0.0
    assert subaccount.accumulated_markup_contribution == 5.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 5.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 5.0

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
        "children": [children_subaccounts[0].pk]
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 5.0
    assert response.json()["parent"]["nominal_value"] == 20.0

    assert response.json()["budget"]["accumulated_markup_contribution"] == 5.0
    assert response.json()["budget"]["nominal_value"] == 20.0


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_budget_markup_child_not_same_parent(api_client, user, context,
        create_account, create_context_budget, create_markup):
    budget = create_context_budget(context=context)
    another_budget = create_context_budget(context=context)
    account = create_account(parent=another_budget, context=context)
    markup = create_markup(parent=budget, percent=True)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [account.pk],
    })
    assert response.status_code == 400


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_update_account_markup_child_not_same_parent(api_client, user,
        create_account, create_context_budget, create_markup, context,
        create_subaccount):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    another_account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=another_account, context=context)
    markup = create_markup(parent=account, percent=True)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [subaccount.pk],
    })
    assert response.status_code == 400


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_delete_budget_markup(api_client, user, create_context_budget, models,
        create_markup, context):
    budget = create_context_budget(context=context)
    markup = create_markup(parent=budget, percent=True)

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markup.pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 0


@pytest.mark.parametrize('context', ['budget', 'template'])
def test_delete_account_markup(api_client, user, create_context_budget,
        models, create_account, create_markup, context):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    markup = create_markup(parent=account, percent=True)

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markup.pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 0
