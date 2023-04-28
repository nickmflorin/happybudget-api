import pytest


def test_get_account_markup(api_client, user, budget_f, f, models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    markup = f.create_markup(parent=budget, accounts=[account])

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
            "name": models.Markup.UNITS[markup.unit].name,
            "slug": models.Markup.UNITS[markup.unit].slug
        },
        "children": [account.pk]
    }


def test_get_subaccount_markup(api_client, user, budget_f, f, models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    markup = f.create_markup(parent=account, subaccounts=[subaccount])

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
            "name": models.Markup.UNITS[markup.unit].name,
            "slug": models.Markup.UNITS[markup.unit].slug
        },
        "children": [subaccount.pk]
    }


def test_update_markup_children(api_client, user, budget_f, f, models):
    budget = budget_f.create_budget()
    markups = [
        f.create_markup(parent=budget, flat=True, rate=20),
        f.create_markup(parent=budget, flat=True, rate=30),
        f.create_markup(parent=budget, percent=True, rate=0.5)
    ]
    accounts = [
        budget_f.create_account(parent=budget, markups=[markups[2]]),
        budget_f.create_account(parent=budget, markups=[markups[2]]),
        budget_f.create_account(parent=budget, markups=[markups[2]])
    ]
    subaccount_sets = [
        budget_f.create_subaccount(
            parent=accounts[0],
            quantity=1,
            rate=10,
            count=2,
        ),
        budget_f.create_subaccount(
            parent=accounts[1],
            quantity=1,
            rate=10,
            count=2,
        ),
        budget_f.create_subaccount(
            parent=accounts[2],
            quantity=1,
            rate=10,
            count=2,

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
            "name": models.Markup.UNITS[markups[0].unit].name,
            "slug": models.Markup.UNITS[markups[0].unit].slug
        },
        "children": [a.pk for a in accounts],
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 90.0
    assert response.json()["parent"]["nominal_value"] == 60.0


def test_update_account_markup_children(api_client, user, budget_f, models, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    markups = [
        f.create_markup(parent=account, flat=True, rate=20),
        f.create_markup(parent=account, percent=True, rate=0.5),
        f.create_markup(parent=account, percent=True, rate=0.5)
    ]
    subaccounts = [
        budget_f.create_subaccount(
            parent=account,
            quantity=1,
            rate=10,
            markups=[markups[1]],
        ),
        budget_f.create_subaccount(
            parent=account,
            quantity=1,
            rate=10,
            markups=[markups[2]],
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
            "name": models.Markup.UNITS[markups[1].unit].name,
            "slug": models.Markup.UNITS[markups[1].unit].slug
        },
        "children": [a.pk for a in subaccounts],
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 35.0
    assert response.json()["parent"]["nominal_value"] == 20.0


def test_update_subaccount_markup_children(api_client, user, budget_f, models,
        f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    markups = [
        f.create_markup(parent=subaccount, flat=True, rate=20),
        f.create_markup(parent=subaccount, percent=True, rate=0.5),
        f.create_markup(parent=subaccount, percent=True, rate=0.5)
    ]
    children_subaccounts = [
        budget_f.create_subaccount(
            parent=subaccount,
            quantity=1,
            rate=10,
            markups=[markups[1]],
        ),
        budget_f.create_subaccount(
            parent=subaccount,
            quantity=1,
            rate=10,
            markups=[markups[2]],
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
            "name": models.Markup.UNITS[markups[1].unit].name,
            "slug": models.Markup.UNITS[markups[1].unit].slug,
        },
        "children": [a.pk for a in children_subaccounts],
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 35.0
    assert response.json()["parent"]["nominal_value"] == 20.0

    assert response.json()["budget"]["accumulated_markup_contribution"] == 35.0
    assert response.json()["budget"]["nominal_value"] == 20.0


def test_update_account_flat_markup_rate(api_client, user, budget_f, models, f):
    budget = budget_f.create_budget()
    markups = [
        f.create_markup(parent=budget, flat=True, rate=20),
        f.create_markup(parent=budget, flat=True, rate=30)
    ]
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    budget_f.create_subaccount(
        parent=accounts[0],
        quantity=1,
        rate=10,
        count=2,
    )
    budget_f.create_subaccount(
        parent=accounts[1],
        quantity=1,
        rate=10,
        count=2,
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
            "name": models.Markup.UNITS[markups[0].unit].name,
            "slug": models.Markup.UNITS[markups[0].unit].slug
        }
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 70.0
    assert response.json()["parent"]["nominal_value"] == 40.0


def test_change_account_flat_markup_to_percent(api_client, user, models,
        budget_f, create_markup):
    budget = budget_f.create_budget()
    markups = [
        create_markup(parent=budget, flat=True, rate=20),
        create_markup(parent=budget, flat=True, rate=30)
    ]
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    budget_f.create_subaccount(
        parent=accounts[0],
        quantity=1,
        rate=10,
        count=2
    )
    budget_f.create_subaccount(
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
        "children": [accounts[1].pk],
        "unit": {
            "id": markups[0].unit,
            "name": models.Markup.UNITS[markups[0].unit].name,
            "slug": models.Markup.UNITS[markups[0].unit].slug
        }
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 40.0
    assert response.json()["parent"]["nominal_value"] == 40.0


@pytest.mark.parametrize('data', [{}, {'children': []}])
def test_change_account_flat_markup_to_percent_no_children(api_client, user,
        models, budget_f, f, data):
    budget = budget_f.create_budget()
    markups = [
        f.create_markup(parent=budget, flat=True, rate=20),
        f.create_markup(parent=budget, flat=True, rate=30)
    ]
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    budget_f.create_subaccount(
        parent=accounts[0],
        quantity=1,
        rate=10,
        count=2
    )
    budget_f.create_subaccount(
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
            'message': (
                'A markup with unit `percent` must have at least 1 child.'),
            'code': 'invalid',
            'field': 'children'
        }]
    }


def test_update_account_percent_markup_rate(api_client, user, budget_f, models,
        f):
    budget = budget_f.create_budget()
    markups = [
        f.create_markup(parent=budget, percent=True, rate=0.5),
        f.create_markup(parent=budget, flat=True, rate=30)
    ]
    accounts = [
        budget_f.create_account(parent=budget, markups=[markups[0]]),
        budget_f.create_account(parent=budget, markups=[markups[0]])
    ]
    budget_f.create_subaccount(
        parent=accounts[0],
        quantity=1,
        rate=10,
        count=2,

    )
    budget_f.create_subaccount(
        parent=accounts[1],
        quantity=1,
        rate=10,
        count=2,

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
            "name": models.Markup.UNITS[markups[0].unit].name,
            "slug": models.Markup.UNITS[markups[0].unit].slug
        },
        "children": [a.pk for a in accounts],
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 54.0
    assert response.json()["parent"]["nominal_value"] == 40.0


def test_change_account_percent_markup_to_flat(api_client, user, models,
        budget_f, f):
    budget = budget_f.create_budget()
    markups = [
        f.create_markup(parent=budget, percent=True, rate=0.5),
        f.create_markup(parent=budget, flat=True, rate=30)
    ]
    accounts = [
        budget_f.create_account(parent=budget, markups=[markups[0]]),
        budget_f.create_account(parent=budget, markups=[markups[0]])
    ]
    budget_f.create_subaccount(
        parent=accounts[0],
        quantity=1,
        rate=10,
        count=2
    )
    budget_f.create_subaccount(
        parent=accounts[1],
        quantity=1,
        rate=10,
        count=2
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
            "name": models.Markup.UNITS[markups[0].unit].name,
            "slug": models.Markup.UNITS[markups[0].unit].slug
        },
    }

    assert response.json()["parent"]["accumulated_markup_contribution"] == 50.0
    assert response.json()["parent"]["nominal_value"] == 40.0


def test_change_account_percent_markup_to_flat_children(api_client, user, models,
        budget_f, f):
    budget = budget_f.create_budget()
    markups = [
        f.create_markup(parent=budget, percent=True, rate=0.5),
        f.create_markup(parent=budget, flat=True, rate=30)
    ]
    accounts = [
        budget_f.create_account(parent=budget, markups=[markups[0]]),
        budget_f.create_account(parent=budget, markups=[markups[0]])
    ]
    another_account = budget_f.create_account(parent=budget)
    budget_f.create_subaccount(
        parent=accounts[0],
        quantity=1,
        rate=10,
        count=2,
    )
    budget_f.create_subaccount(
        parent=accounts[1],
        quantity=1,
        rate=10,
        count=2,
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
            'field': 'children'
        }]
    }


def test_update_budget_markup_child_not_same_parent(api_client, user, budget_f,
        f):
    budget = budget_f.create_budget()
    another_budget = budget_f.create_budget()
    account = budget_f.create_account(parent=another_budget)
    markup = f.create_markup(parent=budget, percent=True)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [account.pk],
    })
    assert response.status_code == 400


def test_update_account_markup_child_not_same_parent(api_client, user, budget_f,
        f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    another_account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=another_account)
    markup = f.create_markup(parent=account, percent=True)

    api_client.force_login(user)
    response = api_client.patch("/v1/markups/%s/" % markup.pk, data={
        'identifier': 'Markup Identifier',
        'children': [subaccount.pk],
    })
    assert response.status_code == 400


def test_delete_budget_flat_markup(api_client, user, models, f):
    budget = f.create_budget()
    markups = [
        f.create_markup(parent=budget, flat=True, rate=100),
        f.create_markup(parent=budget, percent=True, rate=0.1)
    ]
    f.create_actual(owner=markups[0], value=100, budget=budget)
    f.create_actual(owner=markups[1], value=100, budget=budget)
    account = f.create_account(parent=budget, markups=[markups[1]])
    f.create_subaccount(
        count=2,
        rate=10,
        multiplier=1,
        quantity=1,
        parent=account
    )

    account.refresh_from_db()
    assert account.actual == 0.0
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 2.0

    budget.refresh_from_db()
    assert budget.actual == 200.0
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 102.0

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markups[0].pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 1

    account.refresh_from_db()
    assert account.actual == 0.0
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 2.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.actual == 100.0
    assert budget.accumulated_markup_contribution == 2.0


def test_delete_template_flat_markup(api_client, user, models, f):
    budget = f.create_template()
    markups = [
        f.create_markup(parent=budget, flat=True, rate=100),
        f.create_markup(parent=budget, percent=True, rate=0.1)
    ]
    account = f.create_account(parent=budget, markups=[markups[1]])
    f.create_subaccount(
        count=2,
        rate=10,
        multiplier=1,
        quantity=1,
        parent=account
    )

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 2.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 102.0

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markups[0].pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 1

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 2.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 2.0


def test_delete_budget_percent_markup(api_client, user, models, f):
    budget = f.create_budget()
    markups = [
        f.create_markup(parent=budget, flat=True, rate=100),
        f.create_markup(parent=budget, percent=True, rate=0.1)
    ]
    f.create_actual(owner=markups[0], value=100, budget=budget)
    f.create_actual(owner=markups[1], value=100, budget=budget)
    account = f.create_account(parent=budget, markups=[markups[1]])
    f.create_subaccount(
        count=2,
        rate=10,
        multiplier=1,
        quantity=1,
        parent=account
    )

    account.refresh_from_db()
    assert account.actual == 0.0
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 2.0

    budget.refresh_from_db()
    assert budget.actual == 200.0
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 102.0

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markups[1].pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 1

    account.refresh_from_db()
    assert account.actual == 0.0
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.actual == 100.0
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 100.0


def test_delete_template_percent_markup(api_client, user, models, f):
    budget = f.create_template()
    markups = [
        f.create_markup(parent=budget, flat=True, rate=100),
        f.create_markup(parent=budget, percent=True, rate=0.1)
    ]
    account = f.create_account(parent=budget, markups=[markups[1]])
    f.create_subaccount(
        count=2,
        rate=10,
        multiplier=1,
        quantity=1,
        parent=account
    )

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 2.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 102.0

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markups[1].pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 1

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 100.0


def test_delete_budget_account_flat_markup(api_client, user, models, f):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    markups = [
        f.create_markup(parent=account, flat=True, rate=100),
        f.create_markup(parent=account, percent=True, rate=0.1)
    ]
    f.create_actual(owner=markups[0], value=100, budget=budget)
    f.create_actual(owner=markups[1], value=100, budget=budget)
    subaccounts = [
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=account,
            markups=[markups[1]]
        ),
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=account,
            markups=[markups[1]]
        )
    ]

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 1.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 1.0
    assert subaccounts[1].actual == 0.0

    account.refresh_from_db()
    assert account.actual == 200.0
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 102.0

    budget.refresh_from_db()
    assert budget.actual == 200.0
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 102.0

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markups[0].pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 1

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 1.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 1.0
    assert subaccounts[1].actual == 0.0

    account.refresh_from_db()
    assert account.actual == 100.0
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 2.0

    budget.refresh_from_db()
    assert budget.actual == 100.0
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 2.0


def test_delete_template_account_flat_markup(api_client, user, models, f):
    budget = f.create_template()
    account = f.create_account(parent=budget)
    markups = [
        f.create_markup(parent=account, flat=True, rate=100),
        f.create_markup(parent=account, percent=True, rate=0.1)
    ]
    subaccounts = [
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=account,
            markups=[markups[1]]
        ),
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=account,
            markups=[markups[1]]
        )
    ]

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 1.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 1.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 102.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 102.0

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markups[0].pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 1

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 1.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 1.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 2.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 2.0


def test_delete_budget_account_percent_markup(api_client, user, f, models):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    markups = [
        f.create_markup(parent=account, flat=True, rate=100),
        f.create_markup(parent=account, percent=True, rate=0.1)
    ]
    f.create_actual(owner=markups[0], value=100, budget=budget)
    f.create_actual(owner=markups[1], value=100, budget=budget)
    subaccounts = [
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=account,
            markups=[markups[1]]
        ),
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=account,
            markups=[markups[1]]
        )
    ]

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 1.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 1.0
    assert subaccounts[1].actual == 0.0

    account.refresh_from_db()
    assert account.actual == 200.0
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 102.0

    budget.refresh_from_db()
    assert budget.actual == 200.0
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 102.0

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markups[1].pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 1

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 0.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0
    assert subaccounts[1].actual == 0.0

    account.refresh_from_db()
    assert account.actual == 100.0
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 100.0

    budget.refresh_from_db()
    assert budget.actual == 100.0
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 100.0


def test_delete_template_account_percent_markup(api_client, user, f, models):
    budget = f.create_template()
    account = f.create_account(parent=budget)
    markups = [
        f.create_markup(parent=account, flat=True, rate=100),
        f.create_markup(parent=account, percent=True, rate=0.1)
    ]
    subaccounts = [
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=account,
            markups=[markups[1]]
        ),
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=account,
            markups=[markups[1]]
        )
    ]

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 1.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 1.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 102.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 102.0

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markups[1].pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 1

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 100.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 100.0


def test_delete_budget_subaccount_flat_markup(api_client, user, f, models):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    subaccount = f.create_subaccount(parent=account)
    markups = [
        f.create_markup(parent=subaccount, flat=True, rate=100),
        f.create_markup(parent=subaccount, percent=True, rate=0.1)
    ]
    f.create_actual(owner=markups[0], value=100, budget=budget)
    f.create_actual(owner=markups[1], value=100, budget=budget)
    subaccounts = [
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=subaccount,
            markups=[markups[1]]
        ),
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=subaccount,
            markups=[markups[1]]
        )
    ]

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 1.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 1.0
    assert subaccounts[1].actual == 0.0

    subaccount.refresh_from_db()
    assert subaccount.actual == 200.0
    assert subaccount.nominal_value == 20.0
    assert subaccount.markup_contribution == 0.0
    assert subaccount.accumulated_markup_contribution == 102.0

    account.refresh_from_db()
    assert account.actual == 200.0
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 102.0

    budget.refresh_from_db()
    assert budget.actual == 200.0
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 102.0

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markups[0].pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 1

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 1.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 1.0
    assert subaccounts[1].actual == 0.0

    subaccount.refresh_from_db()
    assert subaccount.actual == 100.0
    assert subaccount.nominal_value == 20.0
    assert subaccount.markup_contribution == 0.0
    assert subaccount.accumulated_markup_contribution == 2.0

    account.refresh_from_db()
    assert account.actual == 100.0
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 2.0

    budget.refresh_from_db()
    assert budget.actual == 100.0
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 2.0


def test_delete_budget_subaccount_percent_markup(api_client, user, f, models):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    subaccount = f.create_subaccount(parent=account)
    markups = [
        f.create_markup(parent=subaccount, flat=True, rate=100),
        f.create_markup(parent=subaccount, percent=True, rate=0.1)
    ]
    f.create_actual(owner=markups[0], value=100, budget=budget)
    f.create_actual(owner=markups[1], value=100, budget=budget)
    subaccounts = [
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=subaccount,
            markups=[markups[1]]
        ),
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=subaccount,
            markups=[markups[1]]
        )
    ]

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 1.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 1.0
    assert subaccounts[1].actual == 0.0

    subaccount.refresh_from_db()
    assert subaccount.actual == 200.0
    assert subaccount.nominal_value == 20.0
    assert subaccount.markup_contribution == 0.0
    assert subaccount.accumulated_markup_contribution == 102.0

    account.refresh_from_db()
    assert account.actual == 200.0
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 102.0

    budget.refresh_from_db()
    assert budget.actual == 200.0
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 102.0

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markups[1].pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 1

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 0.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0
    assert subaccounts[1].actual == 0.0

    subaccount.refresh_from_db()
    assert subaccount.actual == 100.0
    assert subaccount.nominal_value == 20.0
    assert subaccount.markup_contribution == 0.0
    assert subaccount.accumulated_markup_contribution == 100.0

    account.refresh_from_db()
    assert account.actual == 100.0
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 100.0

    budget.refresh_from_db()
    assert budget.actual == 100.0
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 100.0


def test_delete_template_subaccount_flat_markup(api_client, user, models, f):
    budget = f.create_template()
    account = f.create_account(parent=budget)
    subaccount = f.create_subaccount(parent=account)
    markups = [
        f.create_markup(parent=subaccount, flat=True, rate=100),
        f.create_markup(parent=subaccount, percent=True, rate=0.1)
    ]
    subaccounts = [
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=subaccount,
            markups=[markups[1]]
        ),
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=subaccount,
            markups=[markups[1]]
        )
    ]

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 1.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 1.0

    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 20.0
    assert subaccount.markup_contribution == 0.0
    assert subaccount.accumulated_markup_contribution == 102.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 102.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 102.0

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markups[0].pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 1

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 1.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 1.0

    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 20.0
    assert subaccount.markup_contribution == 0.0
    assert subaccount.accumulated_markup_contribution == 2.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 2.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 2.0


def test_delete_template_subaccount_percent_markup(api_client, user, models, f):
    budget = f.create_template()
    account = f.create_account(parent=budget)
    subaccount = f.create_subaccount(parent=account)
    markups = [
        f.create_markup(parent=subaccount, flat=True, rate=100),
        f.create_markup(parent=subaccount, percent=True, rate=0.1)
    ]
    subaccounts = [
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=subaccount,
            markups=[markups[1]]
        ),
        f.create_subaccount(
            rate=10,
            multiplier=1,
            quantity=1,
            parent=subaccount,
            markups=[markups[1]]
        )
    ]

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 1.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 1.0

    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 20.0
    assert subaccount.markup_contribution == 0.0
    assert subaccount.accumulated_markup_contribution == 102.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 102.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 102.0

    api_client.force_login(user)
    response = api_client.delete("/v1/markups/%s/" % markups[1].pk)
    assert response.status_code == 204
    assert models.Markup.objects.count() == 1

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0

    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 20.0
    assert subaccount.markup_contribution == 0.0
    assert subaccount.accumulated_markup_contribution == 100.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 100.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 100.0
