import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_update_fringe(api_client, user, create_budget, create_fringe, models):
    api_client.force_login(user)
    budget = create_budget()
    fringe = create_fringe(budget=budget)
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
def test_get_fringe(api_client, user, create_budget, create_fringe, models):
    api_client.force_login(user)
    budget = create_budget()
    fringe = create_fringe(budget=budget)
    response = api_client.get("/v1/fringes/%s/" % fringe.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": fringe.pk,
        "type": "fringe",
        "name": fringe.name,
        "description": fringe.description,
        "created_by": user.pk,
        "created_at": "2020-01-01 00:00:00",
        "updated_by": user.pk,
        "updated_at": "2020-01-01 00:00:00",
        "rate": fringe.rate,
        "cutoff": fringe.cutoff,
        "color": None,
        "unit": {
            "id": fringe.unit,
            "name": models.Fringe.UNITS[fringe.unit]
        },
        "num_times_used": fringe.num_times_used
    }


@pytest.mark.freeze_time('2020-01-01')
def test_delete_fringe(api_client, user, create_budget, create_fringe, models):
    api_client.force_login(user)
    budget = create_budget()
    fringe = create_fringe(budget=budget)
    response = api_client.delete("/v1/fringes/%s/" % fringe.pk)
    assert response.status_code == 204
    assert models.Fringe.objects.first() is None
