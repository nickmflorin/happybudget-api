import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_templates(api_client, user, create_template, staff_user):
    api_client.force_login(user)
    templates = [
        create_template(),
        create_template(),
        create_template(community=True, created_by=staff_user),
        create_template(community=True, created_by=staff_user)
    ]
    response = api_client.get("/v1/templates/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": templates[0].pk,
            "name": templates[0].name,
            "updated_at": "2020-01-01 00:00:00",
            "type": "budget",
            "domain": "template",
            "image": None
        },
        {
            "id": templates[1].pk,
            "name": templates[1].name,
            "updated_at": "2020-01-01 00:00:00",
            "type": "budget",
            "domain": "template",
            "image": None,
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_staff_user_templates(api_client, create_template, staff_user):
    api_client.force_login(staff_user)
    templates = [
        create_template(created_by=staff_user),
        create_template(created_by=staff_user),
        create_template(community=True, created_by=staff_user),
        create_template(community=True, created_by=staff_user)
    ]
    response = api_client.get("/v1/templates/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": templates[0].pk,
            "name": templates[0].name,
            "updated_at": "2020-01-01 00:00:00",
            "type": "budget",
            "domain": "template",
            "image": None,
        },
        {
            "id": templates[1].pk,
            "name": templates[1].name,
            "updated_at": "2020-01-01 00:00:00",
            "type": "budget",
            "domain": "template",
            "image": None,
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_community_templates(api_client, user, create_template, staff_user):
    api_client.force_login(user)
    templates = [
        create_template(community=True, created_by=staff_user),
        create_template(community=True, created_by=staff_user),
        create_template()
    ]
    response = api_client.get("/v1/templates/community/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": templates[0].pk,
            "name": templates[0].name,
            "updated_at": "2020-01-01 00:00:00",
            "type": "budget",
            "domain": "template",
            "image": None,
            "hidden": False,
        },
        {
            "id": templates[1].pk,
            "name": templates[1].name,
            "updated_at": "2020-01-01 00:00:00",
            "type": "budget",
            "domain": "template",
            "image": None,
            "hidden": False,
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_create_template(api_client, user, models):
    api_client.force_login(user)
    response = api_client.post("/v1/templates/", data={
        "name": "Test Name",
    })
    assert response.status_code == 201

    template = models.Template.objects.first()
    assert template is not None
    assert template.name == "Test Name"
    assert response.json() == {
        "id": template.pk,
        "name": "Test Name",
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "template",
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_community_template(api_client, staff_user, models):
    api_client.force_login(staff_user)
    response = api_client.post("/v1/templates/community/", data={
        "name": "Test Name",
    })
    assert response.status_code == 201

    template = models.Template.objects.first()
    assert template is not None
    assert template.name == "Test Name"
    assert template.community is True
    assert response.json() == {
        "id": template.pk,
        "name": "Test Name",
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "template",
        "image": None,
        "hidden": False,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_hidden_community_template(api_client, staff_user, models):
    api_client.force_login(staff_user)
    response = api_client.post("/v1/templates/community/", data={
        "name": "Test Name",
        "hidden": True,
    })
    assert response.status_code == 201
    assert response.json()['hidden'] is True

    template = models.Template.objects.first()
    assert template is not None
    assert template.hidden is True


@pytest.mark.freeze_time('2020-01-01')
def test_create_hidden_non_community_template(api_client, staff_user, models):
    api_client.force_login(staff_user)
    response = api_client.post("/v1/templates/", data={
        "name": "Test Name",
        "hidden": True,
    })
    assert response.status_code == 400
    assert response.json()['errors'] == [{
        'message': 'Only community templates can be hidden/shown.',
        'code': 'invalid',
        'error_type': 'field',
        'field': 'hidden'
    }]


@pytest.mark.freeze_time('2020-01-01')
def test_create_community_template_non_staff_user(api_client, user):
    api_client.force_login(user)
    response = api_client.post("/v1/templates/community/", data={
        "name": "Test Name",
    })
    assert response.status_code == 403
