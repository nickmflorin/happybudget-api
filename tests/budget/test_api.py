import pytest

from greenbudget.lib.utils.dateutils import api_datetime_string
from greenbudget.app.budget.models import Budget


@pytest.mark.freeze_time('2020-01-01')
def test_get_budgets(api_client, user, create_budget, db):
    api_client.force_login(user)
    budgets = [create_budget(), create_budget()]
    response = api_client.get("/v1/budgets/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": budgets[0].pk,
            "name": budgets[0].name,
            "project_number": budgets[0].project_number,
            "production_type": budgets[0].production_type,
            "production_type_name": budgets[0].production_type_name,
            "created_at": "2020-01-01 00:00:00",
            "shoot_date": api_datetime_string(budgets[0].shoot_date),
            "delivery_date": api_datetime_string(budgets[0].delivery_date),
            "build_days": budgets[0].build_days,
            "prelight_days": budgets[0].prelight_days,
            "studio_shoot_days": budgets[0].studio_shoot_days,
            "location_days": budgets[0].location_days,
            "author": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name
            },
        },
        {
            "id": budgets[1].pk,
            "name": budgets[1].name,
            "project_number": budgets[1].project_number,
            "production_type": budgets[1].production_type,
            "production_type_name": budgets[1].production_type_name,
            "created_at": "2020-01-01 00:00:00",
            "shoot_date": api_datetime_string(budgets[1].shoot_date),
            "delivery_date": api_datetime_string(budgets[1].delivery_date),
            "build_days": budgets[1].build_days,
            "prelight_days": budgets[1].prelight_days,
            "studio_shoot_days": budgets[1].studio_shoot_days,
            "location_days": budgets[1].location_days,
            "author": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name
            },
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget(api_client, user, create_budget, db):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "project_number": budget.project_number,
        "production_type": budget.production_type,
        "production_type_name": budget.production_type_name,
        "created_at": "2020-01-01 00:00:00",
        "shoot_date": api_datetime_string(budget.shoot_date),
        "delivery_date": api_datetime_string(budget.delivery_date),
        "build_days": budget.build_days,
        "prelight_days": budget.prelight_days,
        "studio_shoot_days": budget.studio_shoot_days,
        "location_days": budget.location_days,
        "author": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget(api_client, user, db):
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/", data={
        "name": "Test Name",
        "production_type": 1,
    })
    assert response.status_code == 201

    budget = Budget.objects.first()
    assert budget is not None

    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "project_number": budget.project_number,
        "production_type": 1,
        "production_type_name": budget.PRODUCTION_TYPES[1],
        "created_at": "2020-01-01 00:00:00",
        "shoot_date": api_datetime_string(budget.shoot_date),
        "delivery_date": api_datetime_string(budget.delivery_date),
        "build_days": budget.build_days,
        "prelight_days": budget.prelight_days,
        "studio_shoot_days": budget.studio_shoot_days,
        "location_days": budget.location_days,
        "author": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name
        }
    }
