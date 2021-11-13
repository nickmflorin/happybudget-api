import pytest

from greenbudget.app.markup.models import Markup


@pytest.mark.freeze_time('2020-01-01')
def test_get_account_markups(api_client, user, models, budget_f, create_markup):
    budget = budget_f.create_budget()
    markup = create_markup(parent=budget)
    account = budget_f.create_account(parent=budget, markups=[markup])

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/markups/"
        % (budget_f.context, budget.pk)
    )
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
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
    }]


@pytest.mark.freeze_time('2020-01-01')
def test_create_flat_markup(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = budget_f.create_subaccounts(
        parent=account,
        quantity=1,
        rate=10,
        count=2
    )
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

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.post(
        "/v1/%ss/%s/markups/" % (budget_f.context, account.pk),
        data={
            'identifier': 'Markup Identifier',
            'rate': 20,
            'unit': models.Markup.UNITS.flat
        })
    assert response.status_code == 201

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.accumulated_markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 20.0

    markup = models.Markup.objects.first()
    assert markup is not None
    assert markup.identifier == "Markup Identifier"
    # Flat Markup should not have any children.
    assert markup.children.count() == 0
    assert markup.parent == budget

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
        "updated_by": user.pk
    }

    assert response.json()["budget"]["accumulated_markup_contribution"] == 20.0
    assert response.json()["budget"]["nominal_value"] == 20.0


@pytest.mark.freeze_time('2020-01-01')
def test_create_percent_markup(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = budget_f.create_subaccounts(
        parent=account,
        quantity=1,
        rate=10,
        count=2
    )
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

    budget.refresh_from_db()
    assert budget.nominal_value == 20.0
    assert budget.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.post(
        "/v1/%ss/%s/markups/" % (budget_f.context, account.pk),
        data={
            'identifier': 'Markup Identifier',
            'rate': 0.5,
            'unit': models.Markup.UNITS.percent,
            'children': [account.pk],
        })
    assert response.status_code == 201

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 10.0
    assert subaccounts[0].markup_contribution == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 10.0
    assert subaccounts[1].markup_contribution == 0.0

    account.refresh_from_db()
    assert account.nominal_value == 20.0
    assert account.markup_contribution == 10.0
    assert account.accumulated_markup_contribution == 0.0

    budget.refresh_from_db()
    assert budget.accumulated_markup_contribution == 10.0

    markup = models.Markup.objects.first()
    assert markup is not None
    assert markup.identifier == "Markup Identifier"
    assert markup.children.count() == 1
    assert markup.children.all()[0] == account
    assert markup.parent == budget

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
        "children": [account.pk]
    }

    assert response.json()["budget"]["accumulated_markup_contribution"] == 10.0
    assert response.json()["budget"]["nominal_value"] == 20.0


def test_create_percent_markup_invalid_child(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    another_budget = budget_f.create_budget()
    account = budget_f.create_account(parent=another_budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/%ss/%s/markups/" % (budget_f.context, budget.pk),
        data={
            'children': [account.pk],
            'rate': 20,
            'unit': models.Markup.UNITS.percent,
        })
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': (
                'The child account with ID %s either does not exist '
                'or does not belong to the same parent (%s with ID %s) as '
                'the markup.' % (account.id, budget_f.context, budget.id)
            ),
            'code': 'does_not_exist',
            'error_type': 'field',
            'field': 'children'
        }]
    }


@pytest.mark.parametrize('data', [
    {'children': [], 'rate': 20, 'unit': Markup.UNITS.percent},
    {'rate': 20, 'unit': Markup.UNITS.percent}
])
def test_create_percent_markup_no_children(api_client, user, data, budget_f):
    budget = budget_f.create_budget()
    api_client.force_login(user)
    response = api_client.post(
        "/v1/%ss/%s/markups/" % (budget_f.context, budget.pk),
        data=data
    )
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': 'A markup with unit `percent` must have at least 1 child.',  # noqa
            'code': 'invalid',
            'error_type': 'field',
            'field': 'children'
        }]
    }


def test_create_flat_markup_children(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/%ss/%s/markups/" % (budget_f.context, account.pk),
        data={
            'children': [account.pk],
            'rate': 20,
            'unit': models.Markup.UNITS.flat
        })
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': 'A markup with unit `flat` cannot have children.',
            'code': 'invalid',
            'error_type': 'field',
            'field': 'children'
        }]
    }


def test_bulk_delete_markups(api_client, user, models, create_markup, budget_f):
    budget = budget_f.create_budget()
    markups = [
        create_markup(parent=budget, unit=models.Markup.UNITS.flat, rate=100),
        create_markup(parent=budget, unit=models.Markup.UNITS.flat, rate=100),
        create_markup(
            parent=budget,
            unit=models.Markup.UNITS.percent,
            rate=0.5
        )
    ]
    # Markups can only be assigned to an Account/SubAccount if they are percent
    # based.
    account = budget_f.create_account(parent=budget, markups=[markups[2]])
    subaccount = budget_f.create_subaccount(
        parent=account,
        rate=10,
        quantity=10,
        multiplier=1
    )

    assert budget.nominal_value == 100.0
    assert budget.accumulated_markup_contribution == 250.0
    assert account.nominal_value == 100.0
    assert account.markup_contribution == 50.0
    assert account.accumulated_markup_contribution == 0.0
    assert subaccount.nominal_value == 100.0
    assert subaccount.markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/%ss/%s/bulk-delete-markups/" % (budget_f.context, budget.pk),
        data={'ids': [m.pk for m in [markups[0], markups[2]]]}
    )

    assert response.status_code == 200
    assert models.Markup.objects.count() == 1

    budget.refresh_from_db()
    assert budget.nominal_value == 100.0
    assert budget.accumulated_markup_contribution == 100.0

    account.refresh_from_db()
    assert account.nominal_value == 100.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 0.0

    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 100.0
    assert subaccount.markup_contribution == 0.0

    assert response.json()['data']['id'] == budget.pk
    assert response.json()['data']['nominal_value'] == 100.0
    assert response.json()['data']['accumulated_markup_contribution'] == 100.0
    assert response.json()['data']['actual'] == 0.0
