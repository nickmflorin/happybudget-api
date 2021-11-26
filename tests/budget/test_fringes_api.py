def test_get_fringes(api_client, user, create_fringe, models, budget_f):
    budget = budget_f.create_budget()
    fringes = [
        create_fringe(budget=budget),
        create_fringe(budget=budget)
    ]
    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/fringes/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": fringes[0].pk,
            "type": "fringe",
            "name": fringes[0].name,
            "description": fringes[0].description,
            "rate": fringes[0].rate,
            "cutoff": fringes[0].cutoff,
            "color": None,
            "order": "n",
            "unit": {
                "id": fringes[0].unit,
                "name": models.Fringe.UNITS[fringes[0].unit]
            }
        },
        {
            "id": fringes[1].pk,
            "type": "fringe",
            "name": fringes[1].name,
            "description": fringes[1].description,
            "rate": fringes[1].rate,
            "cutoff": fringes[1].cutoff,
            "color": None,
            "order": "t",
            "unit": {
                "id": fringes[1].unit,
                "name": models.Fringe.UNITS[fringes[1].unit]
            }
        },
    ]


def test_create_fringe(api_client, user, budget_f, models):
    budget = budget_f.create_budget()
    api_client.force_login(user)
    response = api_client.post(
        "/v1/%ss/%s/fringes/" % (budget_f.context, budget.pk),
        data={
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
        "type": "fringe",
        "name": "Test Fringe",
        "description": None,
        "rate": 5.5,
        "cutoff": None,
        "color": None,
        "order": "n",
        "unit": {
            "id": 1,
            "name": models.Fringe.UNITS[1]
        }
    }
    assert fringe.name == "Test Fringe"
    assert fringe.rate == 5.5
    assert fringe.cutoff is None
    assert fringe.unit == 1


def test_bulk_create_fringes(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    # Do not disable the signals, because disabling the signals will prevent
    # the metrics on the SubAccount(s) (and thus the Account(s) and Budget) from
    # being calculated.
    budget_f.create_subaccount(
        parent=accounts[0],
        quantity=1,
        rate=100,
        multiplier=1
    )
    budget_f.create_subaccount(
        parent=accounts[1],
        quantity=1,
        rate=100,
        multiplier=1
    )

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/%ss/%s/bulk-create-fringes/" % (budget_f.context, budget.pk),
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
    # the Budget.
    assert response.json()['data']['id'] == budget.pk
    # The Fringe(s) should not have an affect on the calculated value of the
    # Budget because they have not yet been tied to a specific SubAccount.
    assert response.json()['data']['nominal_value'] == 200.0
    assert response.json()['data']['actual'] == 0.0

    # Make sure the actual Fringe(s) were created in the database.
    fringes = models.Fringe.objects.all()
    assert len(fringes) == 2
    assert fringes[0].name == "fringe-a"
    assert fringes[0].rate == 1.2
    assert fringes[0].budget == budget
    assert fringes[1].name == "fringe-b"
    assert fringes[1].rate == 2.2
    assert fringes[1].budget == budget

    # The Fringe(s) should not have an affect on the calculated value of the
    # Budget because they have not yet been tied to a specific SubAccount.
    budget.refresh_from_db()
    assert budget.nominal_value == 200.0
    assert budget.actual == 0.0


def test_bulk_update_fringes(api_client, user, create_fringe, budget_f):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    fringes = [
        create_fringe(budget=budget, rate=0.5),
        create_fringe(budget=budget, rate=0.2)
    ]
    # Do not disable the signals, because disabling the signals will prevent
    # the metrics on the SubAccount(s) (and thus the Account(s) and Budget) from
    # being calculated.
    subaccounts = [
        budget_f.create_subaccount(
            parent=accounts[0],
            quantity=1,
            rate=100,
            multiplier=1,
            fringes=fringes
        ),
        budget_f.create_subaccount(
            parent=accounts[1],
            quantity=2,
            rate=50,
            multiplier=2,
            fringes=fringes
        )
    ]
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].fringe_contribution == 70.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 200.0
    assert subaccounts[1].fringe_contribution == 140.0
    assert subaccounts[1].actual == 0.0

    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 100.0
    assert accounts[0].accumulated_fringe_contribution == 70.0
    assert accounts[0].actual == 0.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 200.0
    assert accounts[1].accumulated_fringe_contribution == 140.0
    assert accounts[1].actual == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 300.0
    assert budget.accumulated_fringe_contribution == 210.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/%ss/%s/bulk-update-fringes/" % (budget_f.context, budget.pk),
        format='json',
        data={'data': [
            {'id': fringes[0].pk, 'rate': 0.7},
            {'id': fringes[1].pk, 'rate': 0.6}
        ]})
    assert response.status_code == 200

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Budget.
    assert response.json()['data']['id'] == budget.pk
    assert response.json()['data']['nominal_value'] == 300.0
    assert response.json()['data']['accumulated_fringe_contribution'] == 390.0
    assert response.json()['data']['actual'] == 0.0

    # Make sure the actual Fringe(s) were updated in the database.
    fringes[0].refresh_from_db()
    assert fringes[0].rate == 0.7
    fringes[1].refresh_from_db()
    assert fringes[1].rate == 0.6

    # Make sure the actual SubAccount(s) were updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].fringe_contribution == 130.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 200.0
    assert subaccounts[1].fringe_contribution == 260.0
    assert subaccounts[1].actual == 0.0

    # Make sure the actual Account(s) were updated in the database.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 100.0
    assert accounts[0].accumulated_fringe_contribution == 130.0
    assert accounts[0].actual == 0.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 200.0
    assert accounts[1].accumulated_fringe_contribution == 260.0
    assert accounts[1].actual == 0.0

    # Make sure the Budget was updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 300.0
    assert budget.accumulated_fringe_contribution == 390.0
    assert budget.actual == 0.0


def test_bulk_delete_fringes(api_client, user, create_fringe, models, budget_f):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    fringes = [
        create_fringe(budget=budget, rate=0.5),
        create_fringe(budget=budget, rate=0.2)
    ]
    # Do not disable the signals, because disabling the signals will prevent
    # the metrics on the SubAccount(s) (and thus the Account(s) and Budget) from
    # being calculated.
    subaccounts = [
        budget_f.create_subaccount(
            parent=accounts[0],
            quantity=1,
            rate=100,
            multiplier=1,
            fringes=fringes
        ),
        budget_f.create_subaccount(
            parent=accounts[1],
            quantity=2,
            rate=50,
            multiplier=2,
            fringes=fringes
        )
    ]
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].fringe_contribution == 70.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 200.0
    assert subaccounts[1].fringe_contribution == 140.0
    assert subaccounts[1].actual == 0.0

    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 100.0
    assert accounts[0].accumulated_fringe_contribution == 70.0
    assert accounts[0].actual == 0.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 200.0
    assert accounts[1].accumulated_fringe_contribution == 140.0
    assert accounts[1].actual == 0.0

    budget.refresh_from_db()
    assert budget.nominal_value == 300.0
    assert budget.accumulated_fringe_contribution == 210.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/%ss/%s/bulk-delete-fringes/" % (budget_f.context, budget.pk),
        data={'ids': [f.pk for f in fringes]}
    )
    assert response.status_code == 200

    # Make sure the Fringe(s) were deleted in the database.
    assert models.Fringe.objects.count() == 0

    # The data in the response refers to base the entity we are updating, A.K.A.
    # the Budget.
    assert response.json()['data']['id'] == budget.pk
    assert response.json()['data']['nominal_value'] == 300.0
    assert response.json()['data']['actual'] == 0.0

    # Make sure the actual SubAccount(s) were updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].fringe_contribution == 0.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 200.0
    assert subaccounts[1].fringe_contribution == 0.0
    assert subaccounts[1].actual == 0.0

    # Make sure the actual Account(s) were updated in the database.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 100.0
    assert accounts[0].accumulated_fringe_contribution == 0.0
    assert accounts[0].actual == 0.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 200.0
    assert accounts[1].accumulated_fringe_contribution == 0.0
    assert accounts[1].actual == 0.0

    # Make sure the Budget was updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 300.0
    assert budget.accumulated_fringe_contribution == 0.0
    assert budget.actual == 0.0
