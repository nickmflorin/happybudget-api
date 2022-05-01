import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_template(api_client, user, f):
    api_client.force_login(user)
    template = f.create_template()
    response = api_client.get("/v1/budgets/%s/" % template.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": template.pk,
        "name": template.name,
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "template",
        "image": None,
        "updated_by": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "email": user.email,
            "profile_image": None
        }
    }


def test_get_another_user_template(api_client, user, f):
    another_user = f.create_user()
    api_client.force_login(user)
    template = f.create_template(created_by=another_user)
    response = api_client.get("/v1/budgets/%s/" % template.pk)
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_get_community_template(api_client, staff_user, f):
    another_staff_user = f.create_user(is_staff=True)
    api_client.force_login(staff_user)
    template = f.create_template(community=True, created_by=another_staff_user)
    response = api_client.get("/v1/budgets/%s/" % template.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": template.pk,
        "name": template.name,
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "template",
        "image": None,
        "hidden": False,
        "updated_by": {
            "id": another_staff_user.id,
            "first_name": another_staff_user.first_name,
            "last_name": another_staff_user.last_name,
            "full_name": another_staff_user.full_name,
            "email": another_staff_user.email,
            "profile_image": None
        }
    }


def test_get_another_users_community_template(api_client, staff_user, f):
    user = f.create_user(is_staff=True)
    template = f.create_template(created_by=user, community=True)
    api_client.force_login(staff_user)
    response = api_client.get("/v1/budgets/%s/" % template.pk, data={
        "name": "New Name"
    })
    assert response.status_code == 200


def test_get_community_template_non_staff_user(api_client, staff_user, user, f):
    api_client.force_login(user)
    template = f.create_template(community=True, created_by=staff_user)
    response = api_client.get("/v1/budgets/%s/" % template.pk)
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_update_template(api_client, user, f):
    template = f.create_template()
    api_client.force_login(user)
    response = api_client.patch("/v1/budgets/%s/" % template.pk, data={
        "name": "New Name"
    })
    assert response.status_code == 200
    template.refresh_from_db()
    assert template.name == "New Name"
    assert response.json() == {
        "id": template.pk,
        "name": "New Name",
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "template",
        "image": None,
        "updated_by": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "email": user.email,
            "profile_image": None
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_community_template(api_client, staff_user, f):
    template = f.create_template(created_by=staff_user, community=True)
    api_client.force_login(staff_user)
    response = api_client.patch("/v1/budgets/%s/" % template.pk, data={
        "name": "New Name"
    })
    assert response.status_code == 200
    template.refresh_from_db()
    assert template.name == "New Name"
    assert response.json() == {
        "id": template.pk,
        "name": "New Name",
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "template",
        "image": None,
        "hidden": False,
        "updated_by": {
            "id": staff_user.id,
            "first_name": staff_user.first_name,
            "last_name": staff_user.last_name,
            "full_name": staff_user.full_name,
            "email": staff_user.email,
            "profile_image": None
        }
    }


def test_hide_community_template(api_client, staff_user, f):
    template = f.create_template(created_by=staff_user, community=True)
    api_client.force_login(staff_user)
    response = api_client.patch("/v1/budgets/%s/" % template.pk, data={
        "name": "New Name",
        "hidden": True
    })
    assert response.status_code == 200
    assert response.json()['hidden'] is True
    template.refresh_from_db()
    assert template.hidden is True


def test_hide_non_community_template(api_client, user, f):
    template = f.create_template()
    api_client.force_login(user)
    response = api_client.patch("/v1/budgets/%s/" % template.pk, data={
        "name": "New Name",
        "hidden": True
    })
    assert response.status_code == 400
    assert response.json()['errors'] == [{
        'message': 'Only community templates can be hidden/shown.',
        'code': 'invalid',
        'error_type': 'field',
        'field': 'hidden'
    }]


@pytest.mark.freeze_time('2020-01-01')
def test_update_another_users_community_template(api_client, staff_user, f):
    user = f.create_user(is_staff=True)
    template = f.create_template(created_by=user, community=True)
    api_client.force_login(staff_user)
    response = api_client.patch("/v1/budgets/%s/" % template.pk, data={
        "name": "New Name"
    })
    assert response.status_code == 200
    template.refresh_from_db()
    assert template.name == "New Name"
    assert response.json() == {
        "id": template.pk,
        "name": "New Name",
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "template",
        "image": None,
        "hidden": False,
        "updated_by": {
            "id": staff_user.id,
            "first_name": staff_user.first_name,
            "last_name": staff_user.last_name,
            "full_name": staff_user.full_name,
            "email": staff_user.email,
            "profile_image": None
        }
    }


def test_make_template_community(api_client, staff_user, f):
    template = f.create_template(created_by=staff_user)
    api_client.force_login(staff_user)
    response = api_client.patch("/v1/budgets/%s/" % template.pk, data={
        "community": True
    })
    assert response.status_code == 200
    template.refresh_from_db()
    assert template.community is True


def test_make_template_community_requires_staff(api_client, staff_user, user, f):
    template = f.create_template(created_by=staff_user)
    api_client.force_login(user)
    response = api_client.patch("/v1/budgets/%s/" % template.pk, data={
        "community": True
    })
    assert response.status_code == 403


def test_update_community_template_non_staff_user(api_client, staff_user, f,
        user):
    template = f.create_template(created_by=staff_user, community=True)
    api_client.force_login(user)
    response = api_client.patch("/v1/budgets/%s/" % template.pk, data={
        "name": "New Name"
    })
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_duplicate_template(api_client, user, f, models):
    original = f.create_template(created_by=user)
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/duplicate/" % original.pk)
    assert models.Template.objects.count() == 2
    template = models.Template.objects.all()[1]

    assert response.status_code == 201
    assert response.json() == {
        "id": template.pk,
        "name": original.name,
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "template",
        "image": None,
        "updated_by": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "email": user.email,
            "profile_image": None
        }
    }


def test_delete_template(api_client, user, f, models):
    api_client.force_login(user)
    template = f.create_template()
    response = api_client.delete("/v1/budgets/%s/" % template.pk)
    assert response.status_code == 204
    assert models.Template.objects.first() is None


def test_delete_community_template(api_client, staff_user, f, models):
    api_client.force_login(staff_user)
    template = f.create_template(created_by=staff_user, community=True)
    response = api_client.delete("/v1/budgets/%s/" % template.pk)
    assert response.status_code == 204
    assert models.Template.objects.first() is None
