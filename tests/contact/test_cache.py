from django.test import override_settings
import pytest


@override_settings(CACHE_ENABLED=True)
def test_cache_invalidated_on_delete(api_client, user, create_contact):
    contacts = [create_contact(), create_contact()]
    api_client.force_login(user)

    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.delete("/v1/contacts/%s/" % contacts[0].pk)
    assert response.status_code == 204

    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
def test_cache_invalidated_on_bulk_delete(api_client, user, create_contact):
    contacts = [create_contact(), create_contact()]
    api_client.force_login(user)

    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/contacts/bulk-delete/",
        data={"ids": [contacts[0].pk]}
    )
    assert response.status_code == 204

    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
@pytest.mark.freeze_time('2020-01-01')
def test_cache_invalidated_on_update(api_client, user, create_contact):
    contacts = [create_contact(), create_contact()]
    api_client.force_login(user)

    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch("/v1/contacts/%s/" % contacts[0].pk, data={
        "first_name": "Jill"
    })
    assert response.status_code == 200

    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['first_name'] == 'Jill'


@override_settings(CACHE_ENABLED=True)
@pytest.mark.freeze_time('2020-01-01')
def test_cache_invalidated_on_bulk_update(api_client, user, create_contact):
    contacts = [create_contact(), create_contact()]
    api_client.force_login(user)

    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/contacts/bulk-update/",
        format='json',
        data={"data": [{"id": contacts[0].pk, "first_name": "Jill"}]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['first_name'] == 'Jill'


@override_settings(CACHE_ENABLED=True)
@pytest.mark.freeze_time('2020-01-01')
def test_cache_invalidated_on_create(api_client, user, create_contact):
    [create_contact(), create_contact()]
    api_client.force_login(user)

    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.post("/v1/contacts/", data={
        "first_name": "Jill"
    })
    assert response.status_code == 201

    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 3


@override_settings(CACHE_ENABLED=True)
@pytest.mark.freeze_time('2020-01-01')
def test_cache_invalidated_on_bulk_create(api_client, user, create_contact):
    [create_contact(), create_contact()]
    api_client.force_login(user)

    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/contacts/bulk-create/",
        format='json',
        data={"data": [{"first_name": "Jill"}]}
    )
    assert response.status_code == 201

    response = api_client.get("/v1/contacts/")
    assert response.status_code == 200
    assert response.json()['count'] == 3
