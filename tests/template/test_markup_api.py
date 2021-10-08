import pytest


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
def test_create_template_markup(api_client, user, create_template_subaccounts,
        create_template_account, create_template, models):
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
    assert account.markup_contribution == 0.0

    template.refresh_from_db()
    assert template.nominal_value == 20.0
    assert template.accumulated_markup_contribution == 0.0

    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/markups/" % template.pk, data={
        'identifier': 'Markup Identifier',
        'rate': 20,
        'unit': models.Markup.UNITS.flat,
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
    assert account.markup_contribution == 20.0

    template.refresh_from_db()
    assert template.accumulated_markup_contribution == 20.0

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

    assert response.json()["budget"]["accumulated_markup_contribution"] == 20.0
    assert response.json()["budget"]["nominal_value"] == 20.0


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_markup_no_children(api_client, user, create_template,
        models):
    template = create_template()
    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/markups/" % template.pk, data={
        'identifier': 'Markup Identifier',
        'rate': 20,
        'unit': models.Markup.UNITS.flat
    })
    assert response.status_code == 400


def test_create_markup_invalid_child(api_client, user,
        create_template_account, create_template):
    template = create_template()
    another_template = create_template()
    account = create_template_account(parent=another_template)

    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/markups/" % template.pk, data={
        'children': [account.pk],
    })
    assert response.status_code == 400


def test_bulk_delete_template_markups(api_client, user, create_template, models,
        create_template_account, create_markup):
    template = create_template()
    markups = [
        create_markup(parent=template, unit=models.Markup.UNITS.flat, rate=100),
        create_markup(parent=template, unit=models.Markup.UNITS.flat, rate=100)
    ]
    account = create_template_account(parent=template, markups=markups)
    assert template.accumulated_markup_contribution == 200.0
    assert account.markup_contribution == 200.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/templates/%s/bulk-delete-markups/" % template.pk,
        data={'ids': [m.pk for m in markups]}
    )

    assert response.status_code == 200
    assert models.Markup.objects.count() == 0

    template.refresh_from_db()
    assert template.accumulated_markup_contribution == 0.0

    account.refresh_from_db()
    assert account.markup_contribution == 0.0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the template.
    assert response.json()['data']['id'] == template.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert response.json()['data']['accumulated_markup_contribution'] == 0.0
    assert response.json()['data']['actual'] == 0.0
