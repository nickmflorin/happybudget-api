import pytest

from greenbudget.app import signals


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_accounts(api_client, user, create_template_account,
        create_template):
    with signals.disable():
        template = create_template()
        accounts = [
            create_template_account(parent=template),
            create_template_account(parent=template)
        ]
    api_client.force_login(user)
    response = api_client.get("/v1/templates/%s/accounts/" % template.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": accounts[0].pk,
            "identifier": "%s" % accounts[0].identifier,
            "description": accounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "type": "account",
            "nominal_value": 0.0,
            "accumulated_value": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "created_by": user.pk,
            "updated_by": user.pk
        },
        {
            "id": accounts[1].pk,
            "identifier": "%s" % accounts[1].identifier,
            "description": accounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "type": "account",
            "nominal_value": 0.0,
            "accumulated_value": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "created_by": user.pk,
            "updated_by": user.pk
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_account(api_client, user, create_template, models):
    template = create_template()
    api_client.force_login(user)
    response = api_client.post(
        "/v1/templates/%s/accounts/" % template.pk,
        data={'identifier': 'new_account'}
    )
    assert response.status_code == 201

    account = models.TemplateAccount.objects.first()
    assert account is not None

    assert response.json() == {
        "id": account.pk,
        "identifier": 'new_account',
        "description": None,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "type": "account",
        "nominal_value": 0.0,
        "accumulated_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "created_by": user.pk,
        "updated_by": user.pk,
    }


def test_bulk_update_template_accounts(api_client, user, create_template,
        create_template_account):
    with signals.disable():
        template = create_template()
        accounts = [
            create_template_account(parent=template),
            create_template_account(parent=template)
        ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/templates/%s/bulk-update-accounts/" % template.pk,
        format='json',
        data={
            'data': [
                {
                    'id': accounts[0].pk,
                    'description': 'New Description 1',
                },
                {
                    'id': accounts[1].pk,
                    'description': 'New Description 2',
                }
            ]
        })
    assert response.status_code == 200

    accounts[0].refresh_from_db()
    assert accounts[0].description == "New Description 1"
    accounts[1].refresh_from_db()
    assert accounts[1].description == "New Description 2"

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Budget.
    assert response.json()['data']['id'] == template.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert response.json()['data']['actual'] == 0.0


def test_bulk_update_template_accounts_outside_template(api_client, user,
        create_template, create_template_account):
    with signals.disable():
        template = create_template()
        another_template = create_template()
        accounts = [
            create_template_account(parent=template),
            create_template_account(parent=another_template)
        ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/templates/%s/bulk-update-accounts/" % template.pk,
        format='json',
        data={
            'data': [
                {
                    'id': accounts[0].pk,
                    'description': 'New Description 1',
                },
                {
                    'id': accounts[1].pk,
                    'description': 'New Description 2',
                }
            ]
        })
    assert response.status_code == 400


def test_bulk_create_template_accounts(api_client, user, create_template,
        models):
    template = create_template()
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/templates/%s/bulk-create-accounts/" % template.pk,
        format='json',
        data={
            'data': [
                {
                    'identifier': 'account-a',
                    'description': 'New Description 1',
                },
                {
                    'identifier': 'account-b',
                    'description': 'New Description 2',
                }
            ]
        })
    assert response.status_code == 201

    accounts = models.Account.objects.all()
    assert len(accounts) == 2
    assert accounts[0].identifier == "account-a"
    assert accounts[0].description == "New Description 1"
    assert accounts[0].budget == template
    assert accounts[1].description == "New Description 2"
    assert accounts[1].identifier == "account-b"
    assert accounts[1].budget == template

    assert len(response.json()['children']) == 2
    assert response.json()['children'][0]['id'] == accounts[0].pk
    assert response.json()['children'][0]['identifier'] == "account-a"
    assert response.json()['children'][0]['description'] == "New Description 1"
    assert response.json()['children'][1]['id'] == accounts[1].pk
    assert response.json()['children'][1]['identifier'] == "account-b"
    assert response.json()['children'][1]['description'] == "New Description 2"

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Budget.
    assert response.json()['data']['id'] == template.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert response.json()['data']['actual'] == 0.0


def test_bulk_delete_template_accounts(api_client, user, create_template,
        create_template_account, create_template_subaccount, models):
    with signals.disable():
        template = create_template()
        accounts = [
            create_template_account(parent=template),
            create_template_account(parent=template)
        ]
    # We need to create SubAccount(s) so that the accounts themselves have
    # calculated values, and thus the Budget itself has calculated values, so
    # we can test whether or not the deletion recalculates the metrics on the
    # Budget.
    create_template_subaccount(
        parent=accounts[0],
        quantity=1,
        rate=100,
        multiplier=1
    )
    create_template_subaccount(
        parent=accounts[1],
        quantity=1,
        rate=100,
        multiplier=1
    )
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/templates/%s/bulk-delete-accounts/" % template.pk, data={
            'ids': [a.pk for a in accounts]
        })
    assert response.status_code == 200
    assert models.TemplateAccount.objects.count() == 0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Budget.
    assert response.json()['data']['id'] == template.pk
    assert response.json()['data']['nominal_value'] == 0.0
    assert response.json()['data']['actual'] == 0.0

    template.refresh_from_db()
    assert template.nominal_value == 0.0
    assert template.actual == 0.0
