import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_header_template(api_client, user, create_header_template):
    template = create_header_template(left_info="<h1>Test</h1>")

    api_client.force_login(user)
    response = api_client.get(
        "/v1/pdf/header-templates/%s/" % template.pk)

    assert response.json() == {
        "id": template.pk,
        "name": template.name,
        "left_image": None,
        "right_image": None,
        "right_info": None,
        "header": None,
        "left_info": "<h1>Test</h1>"
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_header_templates(api_client, user, create_header_template):
    template = create_header_template(left_info="<h1>Test</h1>")
    api_client.force_login(user)
    response = api_client.get("/v1/pdf/header-templates/")
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [
        {
            "id": template.pk,
            "name": template.name,
        }
    ]


def test_create_header_template_empty_field(api_client, user, models):
    api_client.force_login(user)
    response = api_client.post(
        "/v1/pdf/header-templates/",
        format='json',
        data={
            'name': 'Test Header Template',
            'left_info': ""
        })
    assert response.status_code == 201
    assert models.HeaderTemplate.objects.count() == 1
    template = models.HeaderTemplate.objects.first()
    assert template.name == "Test Header Template"
    assert template.left_info is None


def test_create_header_template_non_unique_name(api_client, user,
        create_header_template):
    create_header_template(name="Test Header Template")
    api_client.force_login(user)
    response = api_client.post(
        "/v1/pdf/header-templates/",
        format='json',
        data={'name': 'Test Header Template'}
    )
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_header_template(api_client, user, models):
    api_client.force_login(user)
    response = api_client.post(
        "/v1/pdf/header-templates/",
        format='json',
        data={
            'name': 'Test Header Template',
            'left_info': "<h1>Test</h1>"
        })
    assert response.status_code == 201

    assert models.HeaderTemplate.objects.count() == 1
    template = models.HeaderTemplate.objects.first()
    assert template.left_info == "<h1>Test</h1>"
    assert template.name == "Test Header Template"

    assert response.json() == {
        "id": template.pk,
        "name": template.name,
        "left_image": None,
        "right_image": None,
        "right_info": None,
        "header": None,
        "left_info": "<h1>Test</h1>"
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_header_template(api_client, user, create_header_template,
        models):
    template = create_header_template(left_info="<h1>Test</h1>")

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/pdf/header-templates/%s/" % template.pk,
        format='json',
        data={'left_info': "<h2>Test</h2>"
    })

    assert response.status_code == 200

    assert models.HeaderTemplate.objects.count() == 1
    template = models.HeaderTemplate.objects.first()
    assert template.left_info == "<h2>Test</h2>"

    assert response.json() == {
        "id": template.pk,
        "name": template.name,
        "left_image": None,
        "right_image": None,
        "right_info": None,
        "header": None,
        "left_info": "<h2>Test</h2>"
    }


def test_delete_header_template(api_client, user, create_header_template,
        models):
    template = create_header_template(left_info="<h1>Test</h1>")
    api_client.force_login(user)
    response = api_client.delete("/v1/pdf/header-templates/%s/" % template.pk)

    assert response.status_code == 204
    assert models.HeaderTemplate.objects.count() == 0
