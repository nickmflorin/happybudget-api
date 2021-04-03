import pytest

from greenbudget.app.budget.models import Fringe


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_fringes(api_client, user, create_budget, create_fringe):
    api_client.force_login(user)
    budget = create_budget()
    fringes = [
        create_fringe(budget=budget),
        create_fringe(budget=budget)
    ]
    response = api_client.get("/v1/budgets/%s/fringes/" % budget.pk)
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
            "unit": fringes[0].unit,
            "unit_name": fringes[0].unit_name,
            "num_times_used": fringes[0].num_times_used
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
            "unit": fringes[1].unit,
            "unit_name": fringes[1].unit_name,
            "num_times_used": fringes[1].num_times_used
        },
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_fringe(api_client, user, create_budget, create_fringe):
    api_client.force_login(user)
    budget = create_budget()
    fringe = create_fringe(budget=budget)
    response = api_client.get("/v1/budgets/fringes/%s/" % fringe.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": fringe.pk,
        "name": fringe.name,
        "description": fringe.description,
        "created_by": user.pk,
        "created_at": "2020-01-01 00:00:00",
        "updated_by": user.pk,
        "updated_at": "2020-01-01 00:00:00",
        "rate": fringe.rate,
        "cutoff": fringe.cutoff,
        "unit": fringe.unit,
        "unit_name": fringe.unit_name,
        "num_times_used": fringe.num_times_used
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget_fringe(api_client, user, create_budget, create_fringe):
    api_client.force_login(user)
    budget = create_budget()
    fringe = create_fringe(budget=budget)
    response = api_client.patch("/v1/budgets/fringes/%s/" % fringe.pk, data={
        'name': 'Test Fringe',
        'rate': 5.5,
        'cutoff': 100,
        'unit': 1,
    })
    assert response.status_code == 200
    fringe.refresh_from_db()
    assert response.json() == {
        "id": fringe.pk,
        "name": "Test Fringe",
        "description": fringe.description,
        "created_by": user.pk,
        "created_at": "2020-01-01 00:00:00",
        "updated_by": user.pk,
        "updated_at": "2020-01-01 00:00:00",
        "rate": 5.5,
        "cutoff": 100.0,
        "unit": 1,
        "unit_name": Fringe.UNITS[1],
        "num_times_used": fringe.num_times_used
    }
    assert fringe.name == "Test Fringe"
    assert fringe.rate == 5.5
    assert fringe.cutoff == 100
    assert fringe.unit == 1


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_fringe(api_client, user, create_budget, create_fringe):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.post("/v1/budgets/%s/fringes/" % budget.pk, data={
        'name': 'Test Fringe',
        'rate': 5.5,
        'cutoff': 100,
        'unit': 1,
    })
    assert response.status_code == 201
    fringe = Fringe.objects.first()
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
        "cutoff": 100.0,
        "unit": 1,
        "unit_name": Fringe.UNITS[1],
        "num_times_used": fringe.num_times_used
    }
    assert fringe.name == "Test Fringe"
    assert fringe.rate == 5.5
    assert fringe.cutoff == 100
    assert fringe.unit == 1


@pytest.mark.freeze_time('2020-01-01')
def test_delete_budget_fringe(api_client, user, create_budget, create_fringe):
    api_client.force_login(user)
    budget = create_budget()
    fringe = create_fringe(budget=budget)
    response = api_client.delete("/v1/budgets/fringes/%s/" % fringe.pk)
    assert response.status_code == 204
    assert Fringe.objects.first() is None
