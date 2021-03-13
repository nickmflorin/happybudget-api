import pytest


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
            "city": contacts[1].city,
            "country": contacts[1].country,
            "phone_number": str(contacts[1].phone_number),
            "email": contacts[1].email,
            "full_name": contacts[1].full_name,
        }
    ]
