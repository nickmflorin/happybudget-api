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
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "type": "template",
            "created_by": user.pk,
            "image": None
        },
        {
            "id": templates[1].pk,
            "name": templates[1].name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "type": "template",
            "created_by": user.pk,
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
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "type": "template",
            "created_by": staff_user.pk,
            "image": None,
        },
        {
            "id": templates[1].pk,
            "name": templates[1].name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "type": "template",
            "created_by": staff_user.pk,
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
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "type": "template",
            "created_by": staff_user.pk,
            "image": None,
            "hidden": False,
        },
        {
            "id": templates[1].pk,
            "name": templates[1].name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "type": "template",
            "created_by": staff_user.pk,
            "image": None,
            "hidden": False,
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_template(api_client, user, create_template):
    api_client.force_login(user)
    template = create_template()
    response = api_client.get("/v1/templates/%s/" % template.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": template.pk,
        "name": template.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "estimated": 0.0,
        "type": "template",
        "created_by": user.pk,
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_another_user_template(api_client, user, create_template,
        create_user):
    another_user = create_user()
    api_client.force_login(user)
    template = create_template(created_by=another_user)
    response = api_client.get("/v1/templates/%s/" % template.pk)
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_get_community_template(api_client, staff_user, create_template,
        create_user):
    another_staff_user = create_user(is_staff=True)
    api_client.force_login(staff_user)
    template = create_template(community=True, created_by=another_staff_user)
    response = api_client.get("/v1/templates/%s/" % template.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": template.pk,
        "name": template.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "estimated": 0.0,
        "type": "template",
        "created_by": another_staff_user.pk,
        "image": None,
        "hidden": False,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_another_users_community_template(api_client, staff_user,
        create_template, create_user):
    user = create_user(is_staff=True)
    template = create_template(created_by=user, community=True)
    api_client.force_login(staff_user)
    response = api_client.get("/v1/templates/%s/" % template.pk, data={
         "name": "New Name"
    })
    assert response.status_code == 200


@pytest.mark.freeze_time('2020-01-01')
def test_get_community_template_non_staff_user(api_client, staff_user, user,
        create_template):
    api_client.force_login(user)
    template = create_template(community=True, created_by=staff_user)
    response = api_client.get("/v1/templates/%s/" % template.pk)
    assert response.status_code == 403


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
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "estimated": 0.0,
        "type": "template",
        "created_by": user.pk,
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
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "estimated": 0.0,
        "type": "template",
        "created_by": staff_user.pk,
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


@pytest.mark.freeze_time('2020-01-01')
def test_update_template(api_client, user, create_template):
    template = create_template()
    api_client.force_login(user)
    response = api_client.patch("/v1/templates/%s/" % template.pk, data={
         "name": "New Name"
    })
    assert response.status_code == 200
    template.refresh_from_db()
    assert template.name == "New Name"
    assert response.json() == {
        "id": template.pk,
        "name": "New Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "estimated": 0.0,
        "type": "template",
        "created_by": user.pk,
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_community_template(api_client, staff_user, create_template):
    template = create_template(created_by=staff_user, community=True)
    api_client.force_login(staff_user)
    response = api_client.patch("/v1/templates/%s/" % template.pk, data={
         "name": "New Name"
    })
    assert response.status_code == 200
    template.refresh_from_db()
    assert template.name == "New Name"
    assert response.json() == {
        "id": template.pk,
        "name": "New Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "estimated": 0.0,
        "type": "template",
        "created_by": staff_user.pk,
        "image": None,
        "hidden": False,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_hide_community_template(api_client, staff_user, create_template):
    template = create_template(created_by=staff_user, community=True)
    api_client.force_login(staff_user)
    response = api_client.patch("/v1/templates/%s/" % template.pk, data={
         "name": "New Name",
         "hidden": True
    })
    assert response.status_code == 200
    assert response.json()['hidden'] is True
    template.refresh_from_db()
    assert template.hidden is True


@pytest.mark.freeze_time('2020-01-01')
def test_hide_non_community_template(api_client, user, create_template):
    template = create_template()
    api_client.force_login(user)
    response = api_client.patch("/v1/templates/%s/" % template.pk, data={
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
def test_update_another_users_community_template(api_client, staff_user,
        create_template, create_user):
    user = create_user(is_staff=True)
    template = create_template(created_by=user, community=True)
    api_client.force_login(staff_user)
    response = api_client.patch("/v1/templates/%s/" % template.pk, data={
         "name": "New Name"
    })
    assert response.status_code == 200
    template.refresh_from_db()
    assert template.name == "New Name"
    assert response.json() == {
        "id": template.pk,
        "name": "New Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "estimated": 0.0,
        "type": "template",
        "created_by": user.pk,
        "image": None,
        "hidden": False,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_make_template_community(api_client, staff_user, create_template):
    template = create_template(created_by=staff_user)
    api_client.force_login(staff_user)
    response = api_client.patch("/v1/templates/%s/" % template.pk, data={
         "community": True
    })
    assert response.status_code == 200
    template.refresh_from_db()
    assert template.community is True


@pytest.mark.freeze_time('2020-01-01')
def test_make_template_community_requires_staff(api_client, staff_user, user,
        create_template):
    template = create_template(created_by=staff_user)
    api_client.force_login(user)
    response = api_client.patch("/v1/templates/%s/" % template.pk, data={
         "community": True
    })
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_update_community_template_non_staff_user(api_client, staff_user,
        create_template, user):
    template = create_template(created_by=staff_user, community=True)
    api_client.force_login(user)
    response = api_client.patch("/v1/templates/%s/" % template.pk, data={
         "name": "New Name"
    })
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_duplicate_template(api_client, user, create_template, models):
    original = create_template(created_by=user)
    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/duplicate/" % original.pk)
    assert models.Template.objects.count() == 2
    template = models.Template.objects.all()[1]

    assert response.status_code == 201
    assert response.json() == {
        "id": template.pk,
        "name": original.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "estimated": 0.0,
        "type": "template",
        "created_by": user.pk,
        "image": None,
    }


def test_delete_template(api_client, user, create_template, models):
    api_client.force_login(user)
    template = create_template()
    response = api_client.delete("/v1/templates/%s/" % template.pk)
    assert response.status_code == 204
    assert models.Template.objects.first() is None


def test_delete_community_template(api_client, staff_user, create_template,
        models):
    api_client.force_login(staff_user)
    template = create_template(created_by=staff_user, community=True)
    response = api_client.delete("/v1/templates/%s/" % template.pk)
    assert response.status_code == 204
    assert models.Template.objects.first() is None
