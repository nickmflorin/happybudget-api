def test_update_fringe(api_client, user, budget_f, f, models):
    api_client.force_login(user)
    budget = budget_f.create_budget()
    fringe = f.create_fringe(budget=budget)
    response = api_client.patch("/v1/fringes/%s/" % fringe.pk, data={
        'name': 'Test Fringe',
        'rate': 5.5,
        'cutoff': 100,
        'unit': 1,
    })
    assert response.status_code == 200
    fringe.refresh_from_db()
    assert response.json() == {
        "id": fringe.pk,
        "type": "fringe",
        "name": "Test Fringe",
        "description": fringe.description,
        "rate": 5.5,
        "cutoff": None,
        "color": None,
        "order": "n",
        "unit": {
            "id": 1,
            "name": models.Fringe.UNITS[1].name,
            "slug": models.Fringe.UNITS[1].slug
        }
    }
    assert fringe.name == "Test Fringe"
    assert fringe.rate == 5.5
    assert fringe.cutoff is None
    assert fringe.unit == 1


def test_update_fringe_with_subaccounts(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account, rate=100, quantity=1),
        budget_f.create_subaccount(parent=account, rate=100, quantity=2)
    ]
    fringe = f.create_fringe(budget=budget)
    api_client.force_login(user)
    response = api_client.patch("/v1/fringes/%s/" % fringe.pk, data={
        'subaccounts': [s.pk for s in subaccounts]
    })
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'Field is not allowed for PATCH requests.',
        'code': 'invalid',
        'error_type': 'field',
        'field': 'subaccounts'
    }]}


def test_get_fringe(api_client, user, budget_f, f, models):
    api_client.force_login(user)
    budget = budget_f.create_budget()
    fringe = f.create_fringe(budget=budget)
    response = api_client.get("/v1/fringes/%s/" % fringe.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": fringe.pk,
        "type": "fringe",
        "name": fringe.name,
        "description": fringe.description,
        "rate": fringe.rate,
        "cutoff": fringe.cutoff,
        "color": None,
        "order": "n",
        "unit": {
            "id": fringe.unit,
            "name": models.Fringe.UNITS[fringe.unit].name,
            "slug": models.Fringe.UNITS[fringe.unit].slug
        },
    }


def test_delete_fringe(api_client, user, budget_f, f, models):
    api_client.force_login(user)
    budget = budget_f.create_budget()
    fringe = f.create_fringe(budget=budget)
    response = api_client.delete("/v1/fringes/%s/" % fringe.pk)
    assert response.status_code == 204
    assert models.Fringe.objects.first() is None
