import pytest

from greenbudget.app import signals


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_fringes(api_client, user, create_template, create_fringe,
        models):
    with signals.disable():
        template = create_template()
        fringes = [
            create_fringe(budget=template),
            create_fringe(budget=template)
        ]
    api_client.force_login(user)
    response = api_client.get("/v1/templates/%s/fringes/" % template.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": fringes[0].pk,
            "name": fringes[0].name,
            "description": fringes[0].description,
            "created_by": user.pk,
            "created_at": "2020-01-01 00:00:00",
            "updated_by": user.pk,
            "updated_at": "2020-01-01 00:00:00",
            "rate": fringes[0].rate,
            "cutoff": fringes[0].cutoff,
            "num_times_used": fringes[0].num_times_used,
            "color": None,
            "unit": {
                "id": fringes[0].unit,
                "name": models.Fringe.UNITS[fringes[0].unit]
            }
        },
        {
            "id": fringes[1].pk,
            "name": fringes[1].name,
            "description": fringes[1].description,
            "created_by": user.pk,
            "created_at": "2020-01-01 00:00:00",
            "updated_by": user.pk,
            "updated_at": "2020-01-01 00:00:00",
            "rate": fringes[1].rate,
            "cutoff": fringes[1].cutoff,
            "num_times_used": fringes[1].num_times_used,
            "color": None,
            "unit": {
                "id": fringes[1].unit,
                "name": models.Fringe.UNITS[fringes[1].unit]
            }
        },
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_fringe(api_client, user, create_template, models):
    api_client.force_login(user)
    template = create_template()
    response = api_client.post("/v1/templates/%s/fringes/" % template.pk, data={
        'name': 'Test Fringe',
        'rate': 5.5,
        'cutoff': 100,
        'unit': 1,
    })
    assert response.status_code == 201
    fringe = models.Fringe.objects.first()
    assert fringe is not None
    assert response.json() == {
        "id": fringe.pk,
        "name": "Test Fringe",
        "description": None,
        "created_by": user.pk,
        "created_at": "2020-01-01 00:00:00",
        "updated_by": user.pk,
        "updated_at": "2020-01-01 00:00:00",
        "rate": 5.5,
        "cutoff": None,
        "num_times_used": fringe.num_times_used,
        "color": None,
        "unit": {
            "id": 1,
            "name": models.Fringe.UNITS[1]
        }
    }
    assert fringe.name == "Test Fringe"
    assert fringe.rate == 5.5
    assert fringe.cutoff is None
    assert fringe.unit == 1


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_template_fringes(api_client, user, create_template, models,
        create_template_account, create_template_subaccount):
    template = create_template()
    accounts = [
        create_template_account(budget=template),
        create_template_account(budget=template)
    ]
    # Do not disable the signals, because disabling the signals will prevent
    # the metrics on the SubAccount(s) (and thus the Account(s) and Template)
    # from being calculated.
    create_template_subaccount(
        budget=template,
        parent=accounts[0],
        quantity=1,
        rate=100,
        multiplier=1
    )
    create_template_subaccount(
        budget=template,
        parent=accounts[1],
        estimated=100,
        quantity=1,
        rate=100,
        multiplier=1
    )

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/templates/%s/bulk-create-fringes/" % template.pk,
        format='json',
        data={'data': [
            {'name': 'fringe-a', 'rate': 1.2},
            {'name': 'fringe-b', 'rate': 2.2}
        ]})
    assert response.status_code == 201

    # The children in the response will be the created Fringes.
    assert len(response.json()['children']) == 2
    assert response.json()['children'][0]['name'] == 'fringe-a'
    assert response.json()['children'][0]['rate'] == 1.2
    assert response.json()['children'][1]['name'] == 'fringe-b'
    assert response.json()['children'][1]['rate'] == 2.2

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Template.
    assert response.json()['data']['id'] == template.pk
    # The Fringe(s) should not have an affect on the calculated value of the
    # Template because they have not yet been tied to a specific SubAccount.
    assert response.json()['data']['estimated'] == 200.0

    # Make sure the actual Fringe(s) were created in the database.
    fringes = models.Fringe.objects.all()
    assert len(fringes) == 2
    assert fringes[0].name == "fringe-a"
    assert fringes[0].rate == 1.2
    assert fringes[0].budget == template
    assert fringes[1].name == "fringe-b"
    assert fringes[1].rate == 2.2
    assert fringes[1].budget == template

    # The Fringe(s) should not have an affect on the calculated value of the
    # Template because they have not yet been tied to a specific SubAccount.
    template.refresh_from_db()
    assert template.estimated == 200.0


def test_bulk_update_template_fringes(api_client, user, create_template,
        create_fringe, create_template_account, create_template_subaccount):
    template = create_template()
    accounts = [
        create_template_account(budget=template),
        create_template_account(budget=template)
    ]
    fringes = [
        create_fringe(budget=template, rate=0.5),
        create_fringe(budget=template, rate=0.2)
    ]
    # Do not disable the signals, because disabling the signals will prevent
    # the metrics on the SubAccount(s) (and thus the Account(s) and Template)
    # from being calculated.
    subaccounts = [
        create_template_subaccount(
            budget=template,
            parent=accounts[0],
            quantity=1,
            rate=100,
            multiplier=1,
            fringes=fringes
        ),
        create_template_subaccount(
            budget=template,
            parent=accounts[1],
            quantity=2,
            rate=50,
            multiplier=2,
            fringes=fringes
        )
    ]
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].estimated == 170.0
    subaccounts[1].refresh_from_db()
    assert subaccounts[1].estimated == 340.0

    accounts[0].refresh_from_db()
    assert accounts[0].estimated == 170.0
    accounts[1].refresh_from_db()
    assert accounts[1].estimated == 340.0

    template.refresh_from_db()
    assert template.estimated == 510.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/templates/%s/bulk-update-fringes/" % template.pk,
        format='json',
        data={'data': [
            {'id': fringes[0].pk, 'rate': 0.7},
            {'id': fringes[1].pk, 'rate': 0.6}
        ]})
    assert response.status_code == 200

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Template.
    assert response.json()['data']['id'] == template.pk
    assert response.json()['data']['estimated'] == 690.0

    # Make sure the actual Fringe(s) were updated in the database.
    fringes[0].refresh_from_db()
    assert fringes[0].rate == 0.7
    fringes[1].refresh_from_db()
    assert fringes[1].rate == 0.6

    # Make sure the actual SubAccount(s) were updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].estimated == 230.0
    subaccounts[1].refresh_from_db()
    assert subaccounts[1].estimated == 460.0

    # Make sure the actual Account(s) were updated in the database.
    accounts[0].refresh_from_db()
    assert accounts[0].estimated == 230.0
    accounts[1].refresh_from_db()
    assert accounts[1].estimated == 460.0

    # Make sure the Template was updated in the database.
    template.refresh_from_db()
    assert template.estimated == 690.0


def test_bulk_delete_fringes(api_client, user, create_template, create_fringe,
        models, create_template_account, create_template_subaccount):
    template = create_template()
    accounts = [
        create_template_account(budget=template),
        create_template_account(budget=template)
    ]
    fringes = [
        create_fringe(budget=template, rate=0.5),
        create_fringe(budget=template, rate=0.2)
    ]
    # Do not disable the signals, because disabling the signals will prevent
    # the metrics on the SubAccount(s) (and thus the Account(s) and Template)
    # from being calculated.
    subaccounts = [
        create_template_subaccount(
            budget=template,
            parent=accounts[0],
            quantity=1,
            rate=100,
            multiplier=1,
            fringes=fringes
        ),
        create_template_subaccount(
            budget=template,
            parent=accounts[1],
            quantity=2,
            rate=50,
            multiplier=2,
            fringes=fringes
        )
    ]
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].estimated == 170.0
    subaccounts[1].refresh_from_db()
    assert subaccounts[1].estimated == 340.0

    accounts[0].refresh_from_db()
    assert accounts[0].estimated == 170.0
    accounts[1].refresh_from_db()
    assert accounts[1].estimated == 340.0

    template.refresh_from_db()
    assert template.estimated == 510.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/templates/%s/bulk-delete-fringes/" % template.pk, data={
            'ids': [f.pk for f in fringes]
        })
    assert response.status_code == 200

    # Make sure the Fringe(s) were deleted in the database.
    assert models.Fringe.objects.count() == 0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Template.
    assert response.json()['data']['id'] == template.pk
    assert response.json()['data']['estimated'] == 300.0

    # Make sure the actual SubAccount(s) were updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].estimated == 100.0
    subaccounts[1].refresh_from_db()
    assert subaccounts[1].estimated == 200.0

    # Make sure the actual Account(s) were updated in the database.
    accounts[0].refresh_from_db()
    assert accounts[0].estimated == 100.0
    accounts[1].refresh_from_db()
    assert accounts[1].estimated == 200.0

    # Make sure the Template was updated in the database.
    template.refresh_from_db()
    assert template.estimated == 300.0
