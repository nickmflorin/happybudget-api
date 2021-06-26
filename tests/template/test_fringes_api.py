import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_fringes(api_client, user, create_template, create_fringe,
        models):
    api_client.force_login(user)
    template = create_template()
    fringes = [
        create_fringe(budget=template),
        create_fringe(budget=template)
    ]
    response = api_client.get("/v1/templates/%s/fringes/" % template.pk)
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
            "num_times_used": fringes[0].num_times_used,
            "color": None,
            "unit": {
                "id": fringes[0].unit,
                "name": models.Fringe.UNITS[fringes[0].unit]
            }
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
            "num_times_used": fringes[1].num_times_used,
            "color": None,
            "unit": {
                "id": fringes[1].unit,
                "name": models.Fringe.UNITS[fringes[1].unit]
            }
        },
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_fringe(api_client, user, create_template, models):
    api_client.force_login(user)
    template = create_template()
    response = api_client.post("/v1/templates/%s/fringes/" % template.pk, data={
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
        "name": "Test Fringe",
        "description": None,
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
def test_bulk_create_template_fringes(api_client, user, create_template,
        models):
    api_client.force_login(user)
    template = create_template()
    response = api_client.patch(
        "/v1/templates/%s/bulk-create-fringes/" % template.pk,
        format='json',
        data={
            'data': [
                {
                    'name': 'fringe-a',
                    'rate': 1.2,
                },
                {
                    'name': 'fringe-b',
                    'rate': 2.2,
                }
            ]
        })
    assert response.status_code == 201

    fringes = models.Fringe.objects.all()
    assert len(fringes) == 2
    assert fringes[0].name == "fringe-a"
    assert fringes[0].rate == 1.2
    assert fringes[0].budget == template
    assert fringes[1].name == "fringe-b"
    assert fringes[1].rate == 2.2
    assert fringes[1].budget == template

    assert response.json()['data'][0]['name'] == 'fringe-a'
    assert response.json()['data'][0]['rate'] == 1.2
    assert response.json()['data'][1]['name'] == 'fringe-b'
    assert response.json()['data'][1]['rate'] == 2.2


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_template_fringes(api_client, user, create_template,
        create_fringe):
    api_client.force_login(user)
    template = create_template()
    fringes = [
        create_fringe(budget=template),
        create_fringe(budget=template)
    ]
    response = api_client.patch(
        "/v1/templates/%s/bulk-update-fringes/" % template.pk,
        format='json',
        data={
            'data': [
                {
                    'id': fringes[0].pk,
                    'name': 'New Name 1',
                },
                {
                    'id': fringes[1].pk,
                    'name': 'New Name 2',
                }
            ]
        })
    assert response.status_code == 200

    fringes[0].refresh_from_db()
    assert fringes[0].name == "New Name 1"
    fringes[1].refresh_from_db()
    assert fringes[1].name == "New Name 2"


def test_bulk_delete_fringes(api_client, user, create_template, create_fringe,
        models):
    template = create_template()
    fringes = [
        create_fringe(budget=template),
        create_fringe(budget=template)
    ]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/templates/%s/bulk-delete-fringes/" % template.pk, data={
            'ids': [f.pk for f in fringes]
        })
    assert response.status_code == 200
    assert models.Fringe.objects.count() == 0
