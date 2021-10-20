import pytest

from greenbudget.app import signals
from greenbudget.app.markup.models import Markup


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_account_markups(api_client, user, models,
        create_template_account, create_template, create_markup):
    template = create_template()
    markup = create_markup(parent=template)
    account = create_template_account(parent=template, markups=[markup])

    api_client.force_login(user)
    response = api_client.get("/v1/templates/%s/markups/" % template.pk)
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
def test_create_template_flat_markup(api_client, user, create_template_account,
        create_template_subaccounts, create_template, models):
    template = create_template()
    account = create_template_account(parent=template)
    subaccounts = create_template_subaccounts(
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

    template.refresh_from_db()
    assert template.nominal_value == 20.0
    assert template.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/markups/" % account.pk, data={
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

    template.refresh_from_db()
    assert template.nominal_value == 20.0
    assert template.accumulated_markup_contribution == 20.0

    markup = models.Markup.objects.first()
    assert markup is not None
    assert markup.identifier == "Markup Identifier"
    # Flat Markup should not have any children.
    assert markup.children.count() == 0
    assert markup.parent == template

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
def test_create_template_percent_markup(api_client, user, create_template,
        create_template_account, create_template_subaccounts, models):
    template = create_template()
    account = create_template_account(parent=template)
    subaccounts = create_template_subaccounts(
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

    template.refresh_from_db()
    assert template.nominal_value == 20.0
    assert template.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/markups/" % account.pk, data={
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

    template.refresh_from_db()
    assert template.accumulated_markup_contribution == 10.0

    markup = models.Markup.objects.first()
    assert markup is not None
    assert markup.identifier == "Markup Identifier"
    assert markup.children.count() == 1
    assert markup.children.all()[0] == account
    assert markup.parent == template

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


def test_create_template_percent_markup_invalid_child(api_client, user,
        create_template_account, create_template, models):
    with signals.disable():
        template = create_template()
        another_template = create_template()
        account = create_template_account(parent=another_template)

    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/markups/" % template.pk, data={
        'children': [account.pk],
        'rate': 20,
        'unit': models.Markup.UNITS.percent,
    })
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': (
                'The child account with ID %s either does not exist '
                'or does not belong to the same parent (template with ID %s) as '
                'the markup.' % (account.id, template.id)
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
def test_create_template_percent_markup_no_children(api_client, user, data,
        create_template):
    with signals.disable():
        template = create_template()

    api_client.force_login(user)
    response = api_client.post(
        "/v1/templates/%s/markups/" % template.pk, data=data)
    assert response.status_code == 400
    assert response.json() == {
        'errors': [{
            'message': 'A markup with unit `percent` must have at least 1 child.',  # noqa
            'code': 'invalid',
            'error_type': 'field',
            'field': 'children'
        }]
    }


def test_create_template_template_subaccount_flat_markup_children(api_client,
        user, create_template_account, create_template, models):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)

    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/markups/" % account.pk, data={
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


def test_bulk_delete_template_markups(api_client, user, create_template, models,
        create_template_account, create_markup, create_template_subaccount):
    template = create_template()
    markups = [
        create_markup(parent=template, unit=models.Markup.UNITS.flat, rate=100),
        create_markup(parent=template, unit=models.Markup.UNITS.flat, rate=100),
        create_markup(
            parent=template,
            unit=models.Markup.UNITS.percent,
            rate=0.5
        )
    ]
    # Markups can only be assigned to an Account/SubAccount if they are percent
    # based.
    account = create_template_account(parent=template, markups=[markups[2]])
    subaccount = create_template_subaccount(
        parent=account,
        rate=10,
        quantity=10,
        multiplier=1
    )

    assert template.nominal_value == 100.0
    assert template.accumulated_markup_contribution == 250.0
    assert account.nominal_value == 100.0
    assert account.markup_contribution == 50.0
    assert account.accumulated_markup_contribution == 0.0
    assert subaccount.nominal_value == 100.0
    assert subaccount.markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/templates/%s/bulk-delete-markups/" % template.pk,
        data={'ids': [m.pk for m in [markups[0], markups[2]]]}
    )

    assert response.status_code == 200
    assert models.Markup.objects.count() == 1

    template.refresh_from_db()
    assert template.nominal_value == 100.0
    assert template.accumulated_markup_contribution == 100.0

    account.refresh_from_db()
    assert account.nominal_value == 100.0
    assert account.markup_contribution == 0.0
    assert account.accumulated_markup_contribution == 0.0

    subaccount.refresh_from_db()
    assert subaccount.nominal_value == 100.0
    assert subaccount.markup_contribution == 0.0

    assert response.json()['data']['id'] == template.pk
    assert response.json()['data']['nominal_value'] == 100.0
    assert response.json()['data']['accumulated_markup_contribution'] == 100.0
    assert response.json()['data']['actual'] == 0.0
