def test_create_subaccount_actual(api_client, user, f, models):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    subaccount = f.create_subaccount(parent=account)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/actuals/" % budget.pk,
        format="json",
        data={
            'owner': {"id": subaccount.pk, "type": "subaccount"},
            'value': 20
        }
    )
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "type": "actual",
        "name": None,
        "notes": None,
        "purchase_order": None,
        "date": None,
        "payment_id": None,
        "value": 20.0,
        "actual_type": None,
        "contact": None,
        "attachments": [],
        "order": "n",
        "owner": {
            "id": subaccount.pk,
            "type": "subaccount",
            "identifier": subaccount.identifier,
            "description": subaccount.description
        }
    }
    budget.refresh_from_db()
    assert budget.actual == 20.0

    account.refresh_from_db()
    assert account.actual == 20.0

    subaccount.refresh_from_db()
    assert subaccount.actual == 20.0

    actual = models.Actual.objects.first()
    assert actual is not None
    assert actual.budget == budget
    assert actual.owner == subaccount


def test_create_markup_actual(api_client, user, f, models):
    budget = f.create_budget()
    account = f.create_account(parent=budget)
    markup = f.create_markup(parent=account)
    subaccount = f.create_subaccount(parent=account, markups=[markup])

    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/actuals/" % budget.pk,
        format="json",
        data={
            'owner': {"id": markup.pk, "type": "markup"},
            'value': 20
        }
    )
    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "type": "actual",
        "name": None,
        "notes": None,
        "purchase_order": None,
        "date": None,
        "payment_id": None,
        "value": 20.0,
        "actual_type": None,
        "contact": None,
        "attachments": [],
        "order": "n",
        "owner": {
            "id": markup.pk,
            "type": "markup",
            "identifier": markup.identifier,
            "description": markup.description
        }
    }
    budget.refresh_from_db()
    assert budget.actual == 20.0

    account.refresh_from_db()
    assert account.actual == 20.0

    subaccount.refresh_from_db()
    assert subaccount.actual == 0.0

    markup.refresh_from_db()
    assert markup.actual == 20.0

    actual = models.Actual.objects.first()
    assert actual is not None
    assert actual.budget == budget
    assert actual.owner == markup


def test_bulk_create_actuals(api_client, user, f, models):
    budget = f.create_budget()
    accounts = [
        f.create_account(parent=budget),
        f.create_account(parent=budget)
    ]
    markups = [
        f.create_markup(parent=accounts[0]),
        f.create_markup(parent=accounts[1])
    ]
    subaccounts = [
        f.create_subaccount(
            parent=accounts[0],
            quantity=1,
            rate=100,
            multiplier=1,
            markups=[markups[0]]
        ),
        f.create_subaccount(
            parent=accounts[1],
            quantity=2,
            rate=50,
            multiplier=2,
            markups=[markups[1]]
        )
    ]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-create-actuals/" % budget.pk,
        format='json',
        data={'data': [
            {
                'value': 40.0,
                'owner': {'id': subaccounts[0].pk, 'type': 'subaccount'}
            },
            {
                'value': 30.0,
                'owner': {'id': subaccounts[0].pk, 'type': 'subaccount'}
            },
            {
                'value': 160.0,
                'owner': {'id': subaccounts[1].pk, 'type': 'subaccount'}
            },
            {
                'value': 10.0,
                'owner': {'id': subaccounts[1].pk, 'type': 'subaccount'}
            },
            {
                'value': 50.0,
                'owner': {'id': markups[0].pk, 'type': 'markup'}
            },
            {
                'value': 20.0,
                'owner': {'id': markups[1].pk, 'type': 'markup'}
            },
        ]})

    assert response.status_code == 200

    # The children in the response will be the created Actuals.
    assert len(response.json()['children']) == 6
    assert response.json()['children'][0]['value'] == 40.0
    assert response.json()['children'][0]['owner']['id'] == subaccounts[0].pk

    assert response.json()['children'][1]['value'] == 30.0
    assert response.json()['children'][1]['owner']['id'] == subaccounts[0].pk

    assert response.json()['children'][2]['value'] == 160.0
    assert response.json()['children'][2]['owner']['id'] == subaccounts[1].pk

    assert response.json()['children'][3]['value'] == 10.0
    assert response.json()['children'][3]['owner']['id'] == subaccounts[1].pk

    assert response.json()['children'][4]['value'] == 50.0
    assert response.json()['children'][4]['owner']['id'] == markups[0].pk

    assert response.json()['children'][5]['value'] == 20.0
    assert response.json()['children'][5]['owner']['id'] == markups[1].pk

    assert response.json()['parent']['id'] == budget.pk
    assert response.json()['parent']['nominal_value'] == 300.0
    assert response.json()['parent']['actual'] == 310.0

    # Make sure the actual Actual(s) were created in the database.
    actuals = models.Actual.objects.all()
    assert len(actuals) == 6
    for actual in actuals:
        assert actual.budget == budget
        assert actual.created_by == user
        assert actual.updated_by == user

    assert actuals[0].value == 40.0
    assert actuals[0].owner == subaccounts[0]
    assert actuals[1].value == 30.0
    assert actuals[1].owner == subaccounts[0]
    assert actuals[2].value == 160.0
    assert actuals[2].owner == subaccounts[1]
    assert actuals[3].value == 10.0
    assert actuals[3].owner == subaccounts[1]
    assert actuals[4].value == 50.0
    assert actuals[4].owner == markups[0]
    assert actuals[5].value == 20.0
    assert actuals[5].owner == markups[1]

    # Make sure the actual SubAccount(s) were updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].actual == 70.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 200.0
    assert subaccounts[1].actual == 170.0

    # Make sure the actual Account(s) were updated in the database.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 100.0
    assert accounts[0].actual == 120.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 200.0
    assert accounts[1].actual == 190.0

    # Make sure the Budget was updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 300.0
    assert budget.actual == 310.0


def test_bulk_update_actuals(api_client, user, f):
    budget = f.create_budget()
    accounts = [
        f.create_account(parent=budget),
        f.create_account(parent=budget)
    ]
    markups = [
        f.create_markup(parent=accounts[0]),
        f.create_markup(parent=accounts[1])
    ]
    subaccounts = [
        f.create_subaccount(
            parent=accounts[0],
            quantity=1,
            rate=100,
            multiplier=1,
            markups=[markups[0]]
        ),
        f.create_subaccount(
            parent=accounts[1],
            quantity=2,
            rate=50,
            multiplier=2,
            markups=[markups[1]]
        )
    ]
    actuals = [
        f.create_actual(owner=subaccounts[0], budget=budget, value=40.0),
        f.create_actual(owner=subaccounts[0], budget=budget, value=30.0),
        f.create_actual(owner=subaccounts[1], budget=budget, value=160.0),
        f.create_actual(owner=subaccounts[1], budget=budget, value=10.0),
        f.create_actual(owner=markups[0], budget=budget, value=20.0),
        f.create_actual(owner=markups[0], budget=budget, value=10.0),
        f.create_actual(owner=markups[1], budget=budget, value=50.0),
        f.create_actual(owner=markups[1], budget=budget, value=40.0),
    ]
    # Make sure everything is calculated correctly before updating via the API
    # so we can more clearly understand why an error might occur.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].actual == 30.0 + 40.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 200.0
    assert subaccounts[1].actual == 160.0 + 10.0

    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 100.0
    assert accounts[0].actual == 30.0 + 40.0 + 20.0 + 10.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 200.0
    assert accounts[1].actual == 160.0 + 10.0 + 50.0 + 40.0

    budget.refresh_from_db()
    assert budget.nominal_value == 300.0
    assert budget.actual == 360.0

    new_values = [30.0, 20.0, 150.0, 0.0, 50.0, 0.0, 15.0, 25.0]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-actuals/" % budget.pk,
        format='json',
        data={'data': [{"id": a.pk, "value": new_values[i]}
            for i, a in enumerate(actuals)]}
    )

    assert response.status_code == 200

    assert response.json()['parent']['id'] == budget.pk
    assert response.json()['parent']['nominal_value'] == 300.0
    assert response.json()['parent']['actual'] == sum(new_values)

    # Make sure the actual Actual(s) were updated in the database.
    for i, actual in enumerate(actuals):
        actual.refresh_from_db()
        assert actual.value == new_values[i], \
            "Actual {pk} value expected to be {new_value}, instead is " \
            "{real_value}.".format(
                real_value=actual.value,
                new_value=new_values[i],
                pk=actual.pk
        )

    # Make sure the actual SubAccount(s) were updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].actual == 30.0 + 20.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 200.0
    assert subaccounts[1].actual == 150.0 + 0.0

    # Make sure the actual Account(s) were updated in the database.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 100.0
    assert accounts[0].actual == 30.0 + 20.0 + 50.0 + 0.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 200.0
    assert accounts[1].actual == 150.0 + 0.0 + 15.0 + 25.0

    # Make sure the Budget was updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 300.0
    assert budget.actual == 290.0


def test_change_actual_owner_in_bulk_update(api_client, user, f):
    budget = f.create_budget()
    accounts = [
        f.create_account(parent=budget),
        f.create_account(parent=budget)
    ]
    markups = [
        f.create_markup(parent=accounts[0]),
        f.create_markup(parent=accounts[1])
    ]
    subaccounts = [
        f.create_subaccount(
            parent=accounts[0],
            quantity=1,
            rate=100,
            multiplier=1,
        ),
        f.create_subaccount(
            parent=accounts[1],
            quantity=2,
            rate=50,
            multiplier=2,
        )
    ]
    actuals = [
        f.create_actual(owner=subaccounts[0], budget=budget, value=40.0),
        f.create_actual(owner=subaccounts[0], budget=budget, value=30.0),
        f.create_actual(owner=subaccounts[1], budget=budget, value=160.0),
        f.create_actual(owner=subaccounts[1], budget=budget, value=10.0),
        f.create_actual(owner=markups[0], budget=budget, value=20.0),
        f.create_actual(owner=markups[0], budget=budget, value=10.0),
        f.create_actual(owner=markups[1], budget=budget, value=50.0),
        f.create_actual(owner=markups[1], budget=budget, value=40.0),
    ]
    # Make sure everything is calculated correctly before updating via the API
    # so we can more clearly understand why an error might occur.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].actual == 30.0 + 40.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 200.0
    assert subaccounts[1].actual == 160.0 + 10.0

    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 100.0
    assert accounts[0].actual == 30.0 + 40.0 + 20.0 + 10.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 200.0
    assert accounts[1].actual == 160.0 + 10.0 + 50.0 + 40.0

    budget.refresh_from_db()
    assert budget.nominal_value == 300.0
    assert budget.actual == 360.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-update-actuals/" % budget.pk,
        format='json',
        data={'data': [{
            "id": actuals[0].pk,
            "owner": {
                "id": markups[0].pk,
                "type": "markup"
            }
        }]}
    )

    assert response.status_code == 200
    actuals[0].refresh_from_db()
    assert actuals[0].owner == markups[0]

    markups[0].refresh_from_db()
    assert markups[0].actual == 70.0

    subaccounts[0].refresh_from_db()
    assert subaccounts[0].actual == 30.0

    assert response.json()['parent']['id'] == budget.pk
    assert response.json()['parent']['nominal_value'] == 300.0
    assert response.json()['parent']['actual'] == 360.0

    # Make sure the actual SubAccount(s) were updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].actual == 30.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 200.0
    assert subaccounts[1].actual == 160.0 + 10.0

    # Make sure the actual Account(s) were updated in the database.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 100.0
    assert accounts[0].actual == 30.0 + 40.0 + 20.0 + 10.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 200.0
    assert accounts[1].actual == 160.0 + 10.0 + 50.0 + 40.0

    # Make sure the Budget was updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 300.0
    assert budget.actual == 360.0


def test_bulk_delete_actuals(api_client, user, models, f):
    budget = f.create_budget()
    accounts = [
        f.create_account(parent=budget),
        f.create_account(parent=budget)
    ]
    markups = [
        f.create_markup(parent=accounts[0]),
        f.create_markup(parent=accounts[1])
    ]
    subaccounts = [
        f.create_subaccount(
            parent=accounts[0],
            quantity=1,
            rate=100,
            multiplier=1,
            markups=[markups[0]]
        ),
        f.create_subaccount(
            parent=accounts[1],
            quantity=2,
            rate=50,
            multiplier=2,
            markups=[markups[1]]
        )
    ]
    actuals = [
        f.create_actual(owner=subaccounts[0], budget=budget, value=40.0),
        f.create_actual(owner=subaccounts[0], budget=budget, value=30.0),
        f.create_actual(owner=subaccounts[1], budget=budget, value=160.0),
        f.create_actual(owner=subaccounts[1], budget=budget, value=10.0),
        f.create_actual(owner=markups[0], budget=budget, value=20.0),
        f.create_actual(owner=markups[0], budget=budget, value=10.0),
        f.create_actual(owner=markups[1], budget=budget, value=50.0),
        f.create_actual(owner=markups[1], budget=budget, value=40.0),
    ]

    # Make sure everything is calculated correctly before updating via the API
    # so we can more clearly understand why an error might occur.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].actual == 30.0 + 40.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 200.0
    assert subaccounts[1].actual == 160.0 + 10.0

    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 100.0
    assert accounts[0].actual == 30.0 + 40.0 + 20.0 + 10.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 200.0
    assert accounts[1].actual == 160.0 + 10.0 + 50.0 + 40.0

    budget.refresh_from_db()
    assert budget.nominal_value == 300.0
    assert budget.actual == 360.0

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-delete-actuals/" % budget.pk, data={
            'ids': [actuals[0].pk, actuals[1].pk, actuals[3].pk, actuals[6].pk]
        })
    assert response.status_code == 200

    # Make sure the Actual(s) were deleted in the database.
    assert models.Actual.objects.count() == 4

    # Make sure the actual SubAccount(s) were updated in the database.
    subaccounts[0].refresh_from_db()
    assert subaccounts[0].nominal_value == 100.0
    assert subaccounts[0].actual == 0.0

    subaccounts[1].refresh_from_db()
    assert subaccounts[1].nominal_value == 200.0
    assert subaccounts[1].actual == 160.0

    # Make sure the actual Account(s) were updated in the database.
    accounts[0].refresh_from_db()
    assert accounts[0].nominal_value == 100.0
    assert accounts[0].actual == 20.0 + 10.0

    accounts[1].refresh_from_db()
    assert accounts[1].nominal_value == 200.0
    assert accounts[1].actual == 160.0 + 40.0

    # Make sure the Budget was updated in the database.
    budget.refresh_from_db()
    assert budget.nominal_value == 300.0
    assert budget.actual == 230.0

    assert response.json()['parent']['id'] == budget.pk
    assert response.json()['parent']['nominal_value'] == 300.0
    assert response.json()['parent']['actual'] == 230.0
