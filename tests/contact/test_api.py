import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_contact(api_client, user, create_contact, models):
    contact = create_contact()
    api_client.force_login(user)
    response = api_client.get("/v1/contacts/%s/" % contact.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": contact.pk,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "city": contact.city,
        "rate": contact.rate,
        "phone_number": contact.phone_number,
        "email": contact.email,
        "full_name": contact.full_name,
        "company": contact.company,
        "position": contact.position,
        "image": None,
        "type": {
            "id": contact.type,
            "name": models.Contact.TYPES[contact.type]
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_contacts(api_client, user, create_contact, models):
    contacts = [create_contact(), create_contact()]
    api_client.force_login(user)
    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": contacts[0].pk,
            "first_name": contacts[0].first_name,
            "last_name": contacts[0].last_name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "city": contacts[0].city,
            "rate": contacts[0].rate,
            "company": contacts[0].company,
            "phone_number": contacts[0].phone_number,
            "email": contacts[0].email,
            "full_name": contacts[0].full_name,
            "position": contacts[0].position,
            "image": None,
            "type": {
                "id": contacts[0].type,
                "name": models.Contact.TYPES[contacts[0].type]
            }
        },
        {
            "id": contacts[1].pk,
            "first_name": contacts[1].first_name,
            "last_name": contacts[1].last_name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "city": contacts[1].city,
            "rate": contacts[1].rate,
            "company": contacts[1].company,
            "phone_number": contacts[1].phone_number,
            "email": contacts[1].email,
            "full_name": contacts[1].full_name,
            "position": contacts[1].position,
            "image": None,
            "type": {
                "id": contacts[1].type,
                "name": models.Contact.TYPES[contacts[1].type]
            }
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_create_contact(api_client, user, models):
    api_client.force_login(user)
    response = api_client.post("/v1/contacts/", data={
        'city': 'New York',
        'rate': 5,
        'first_name': 'Jack',
        'last_name': 'Johnson',
        'type': 1,
        'phone_number': '15183696530',
        'email': 'jjohnson@gmail.com',
        "company": "Boeing"
    })
    assert response.status_code == 201
    contact = models.Contact.objects.first()

    assert contact is not None
    assert contact.city == "New York"
    assert contact.rate == 5
    assert contact.first_name == "Jack"
    assert contact.last_name == "Johnson"
    assert contact.type == 1
    assert contact.phone_number == 15183696530
    assert contact.email == "jjohnson@gmail.com"
    assert contact.company == "Boeing"

    assert response.json() == {
        "id": contact.pk,
        "first_name": "Jack",
        "last_name": "Johnson",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "city": "New York",
        "rate": 5,
        "phone_number": 15183696530,
        "email": "jjohnson@gmail.com",
        "full_name": "Jack Johnson",
        "company": "Boeing",
        "position": None,
        "image": None,
        "type": {
            "id": 1,
            "name": models.Contact.TYPES[1]
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_blank_contact(api_client, user, models):
    api_client.force_login(user)
    response = api_client.post("/v1/contacts/", data={})
    assert response.status_code == 201
    contact = models.Contact.objects.first()

    assert contact is not None
    assert contact.city is None
    assert contact.rate is None
    assert contact.first_name is None
    assert contact.last_name is None
    assert contact.type is None
    assert contact.phone_number is None
    assert contact.email is None
    assert contact.company is None

    assert response.json() == {
        "id": contact.pk,
        "first_name": None,
        "last_name": None,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "company": None,
        "city": None,
        "rate": None,
        "phone_number": None,
        "email": None,
        "full_name": "",
        "type": None,
        "position": None,
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_contact(api_client, user, create_contact, models):
    contact = create_contact()
    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/%s/" % contact.pk, data={
        'city': 'New York',
        'rate': 5,
        'first_name': 'Jack',
        'last_name': 'Johnson',
    })
    assert response.status_code == 200
    contact.refresh_from_db()

    assert contact.city == "New York"
    assert contact.rate == 5
    assert contact.first_name == "Jack"
    assert contact.last_name == "Johnson"

    assert response.json() == {
        "id": contact.pk,
        "first_name": "Jack",
        "last_name": "Johnson",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "city": "New York",
        "rate": 5,
        "company": contact.company,
        "phone_number": contact.phone_number,
        "email": contact.email,
        "full_name": contact.full_name,
        "position": contact.position,
        "image": None,
        "type": {
            "id": contact.type,
            "name": models.Contact.TYPES[contact.type]
        }
    }


def test_delete_contact(api_client, user, create_contact, models):
    contact = create_contact()
    api_client.force_login(user)
    response = api_client.delete("/v1/contacts/%s/" % contact.pk)
    assert response.status_code == 204
    assert models.Contact.objects.first() is None


def test_bulk_delete_contacts(api_client, user, create_contact, models):
    contacts = [create_contact(), create_contact()]
    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/bulk-delete/", data={
        'ids': [c.pk for c in contacts]
    })
    assert response.status_code == 204
    assert models.Contact.objects.count() == 0


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_contacts(api_client, user, models):
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/contacts/bulk-create/",
        format='json',
        data={"data": [
            {
                'city': 'New York',
                'rate': 5,
                'first_name': 'Jack',
                'last_name': 'Johnson',
                'type': 1,
            },
            {
                'phone_number': '15183696530',
                'email': 'jjohnson@gmail.com',
                "company": "Boeing"
            }
        ]}
    )
    assert response.status_code == 201
    assert models.Contact.objects.count() == 2
    contacts = models.Contact.objects.all()
    assert response.json()['data'] == [
        {
            "id": contacts[0].pk,
            "first_name": "Jack",
            "last_name": "Johnson",
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "city": "New York",
            "rate": 5,
            "company": contacts[0].company,
            "phone_number": contacts[0].phone_number,
            "email": contacts[0].email,
            "full_name": contacts[0].full_name,
            "position": contacts[0].position,
            "image": None,
            "type": {
                "id": 1,
                "name": models.Contact.TYPES[1]
            }
        },
        {
            "id": contacts[1].pk,
            "first_name": contacts[1].first_name,
            "last_name": contacts[1].last_name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "city": contacts[1].city,
            "rate": contacts[1].rate,
            "company": "Boeing",
            "phone_number": 15183696530,
            "email": 'jjohnson@gmail.com',
            "full_name": contacts[1].full_name,
            "position": contacts[1].position,
            "image": None,
            "type": None
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_update_contacts(api_client, user, create_contact, models):
    contacts = [create_contact(), create_contact()]
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/contacts/bulk-update/",
        format='json',
        data={'data': [
            {
                'id': contacts[0].pk,
                'city': 'New York',
                'rate': 5,
                'first_name': 'Jack',
                'last_name': 'Johnson',
            },
            {
                'id': contacts[1].pk,
                'phone_number': '15183696530',
                'email': 'jjohnson@gmail.com',
                "company": "Boeing"
            }
        ]})
    assert response.status_code == 200
    [c.refresh_from_db() for c in contacts]

    assert contacts[0].city == "New York"
    assert contacts[0].rate == 5
    assert contacts[0].first_name == "Jack"
    assert contacts[0].last_name == "Johnson"

    assert contacts[1].phone_number == 15183696530
    assert contacts[1].email == 'jjohnson@gmail.com'
    assert contacts[1].company == "Boeing"
