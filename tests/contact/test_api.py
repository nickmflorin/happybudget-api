import pytest

from greenbudget.app.contact.models import Contact


@pytest.mark.freeze_time('2020-01-01')
def test_get_contact(api_client, user, create_contact):
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
        "role": contact.role,
        "role_name": contact.ROLES[contact.role],
        "city": contact.city,
        "country": contact.country,
        "phone_number": str(contact.phone_number),
        "email": contact.email,
        "full_name": contact.full_name,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_contacts(api_client, user, create_contact):
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
            "role": contacts[0].role,
            "role_name": Contact.ROLES[contacts[0].role],
            "city": contacts[0].city,
            "country": contacts[0].country,
            "phone_number": str(contacts[0].phone_number),
            "email": contacts[0].email,
            "full_name": contacts[0].full_name,
        },
        {
            "id": contacts[1].pk,
            "first_name": contacts[1].first_name,
            "last_name": contacts[1].last_name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "role": contacts[1].role,
            "role_name": Contact.ROLES[contacts[1].role],
            "city": contacts[1].city,
            "country": contacts[1].country,
            "phone_number": str(contacts[1].phone_number),
            "email": contacts[1].email,
            "full_name": contacts[1].full_name,
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_create_contact(api_client, user):
    api_client.force_login(user)
    response = api_client.post("/v1/contacts/", data={
        'city': 'New York',
        'country': 'United States',
        'first_name': 'Jack',
        'last_name': 'Johnson',
        'role': 1,
        'phone_number': '+15183696530',
        'email': 'jjohnson@gmail.com',
    })
    assert response.status_code == 201
    contact = Contact.objects.first()

    assert contact is not None
    assert contact.city == "New York"
    assert contact.country == "United States"
    assert contact.first_name == "Jack"
    assert contact.last_name == "Johnson"
    assert contact.role == 1
    assert str(contact.phone_number) == "+15183696530"
    assert contact.email == "jjohnson@gmail.com"

    assert response.json() == {
        "id": contact.pk,
        "first_name": "Jack",
        "last_name": "Johnson",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "role": 1,
        "role_name": Contact.ROLES[contact.role],
        "city": "New York",
        "country": "United States",
        "phone_number": "+15183696530",
        "email": "jjohnson@gmail.com",
        "full_name": "Jack Johnson",
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_contact(api_client, user, create_contact):
    contact = create_contact()
    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/%s/" % contact.pk, data={
        'city': 'New York',
        'country': 'United States',
        'first_name': 'Jack',
        'last_name': 'Johnson',
    })
    assert response.status_code == 200
    contact.refresh_from_db()

    assert contact.city == "New York"
    assert contact.country == "United States"
    assert contact.first_name == "Jack"
    assert contact.last_name == "Johnson"

    assert response.json() == {
        "id": contact.pk,
        "first_name": "Jack",
        "last_name": "Johnson",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "role": contact.role,
        "role_name": Contact.ROLES[contact.role],
        "city": "New York",
        "country": "United States",
        "phone_number": str(contact.phone_number),
        "email": contact.email,
        "full_name": contact.full_name
    }


@pytest.mark.freeze_time('2020-01-01')
def test_delete_contact(api_client, user, create_contact):
    contact = create_contact()
    api_client.force_login(user)
    response = api_client.delete("/v1/contacts/%s/" % contact.pk)
    assert response.status_code == 204
    assert Contact.objects.first() is None
