import pytest

from django.test import override_settings


@pytest.mark.freeze_time('2020-01-01')
@override_settings(APP_URL="https://api.greenbudget.com")
def test_attachments_properly_serializes(api_client, user, create_contact,
        create_attachment):
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg')
    ]
    contact = create_contact(attachments=attachments)
    api_client.force_login(user)
    response = api_client.get("/v1/contacts/%s/" % contact.pk)
    assert response.status_code == 200
    assert 'attachments' in response.json()
    assert response.json()['attachments'] == [
        {
            'id': attachments[0].pk,
            'name': 'attachment1.jpeg',
            'extension': 'jpeg',
            'url': (
                'https://api.greenbudget.com'
                '/media/users/1/attachments/attachment1.jpeg'
            )
        },
        {
            'id': attachments[1].pk,
            'name': 'attachment2.jpeg',
            'extension': 'jpeg',
            'url': (
                'https://api.greenbudget.com'
                '/media/users/1/attachments/attachment2.jpeg'
            )
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
@override_settings(APP_URL="https://api.greenbudget.com")
def test_get_attachments(api_client, user, create_attachment, create_contact):
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg')
    ]
    contact = create_contact(attachments=attachments)
    api_client.force_login(user)
    response = api_client.get("/v1/contacts/%s/attachments/" % contact.pk)
    assert response.status_code == 200

    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            'id': attachments[0].pk,
            'name': 'attachment1.jpeg',
            'extension': 'jpeg',
            'size': 823,
            'url': (
                'https://api.greenbudget.com/'
                'media/users/1/attachments/attachment1.jpeg'
            )
        },
        {
            'id': attachments[1].pk,
            'name': 'attachment2.jpeg',
            'extension': 'jpeg',
            'size': 823,
            'url': (
                'https://api.greenbudget.com/'
                'media/users/1/attachments/attachment2.jpeg'
            )
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_delete_attachment(api_client, user, create_attachment, create_contact):
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg')
    ]
    contact = create_contact(attachments=attachments)
    api_client.force_login(user)
    response = api_client.delete("/v1/contacts/%s/attachments/%s/" % (
        contact.pk, attachments[0].pk))
    assert response.status_code == 204
    assert contact.attachments.count() == 1


@pytest.mark.freeze_time('2020-01-01')
@override_settings(APP_URL="https://api.greenbudget.com")
def test_update_attachments(api_client, user, create_attachment, create_contact):
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg')
    ]
    contact = create_contact(attachments=attachments)
    additional_attachment = create_attachment(name='attachment3.jpeg')
    api_client.force_login(user)
    response = api_client.patch("/v1/contacts/%s/" % contact.pk, data={
        'attachments': [a.pk for a in attachments] + [additional_attachment.pk]
    })
    assert response.status_code == 200

    contact.refresh_from_db()
    assert contact.attachments.count() == 3

    assert 'attachments' in response.json()
    assert response.json()['attachments'] == [
        {
            'id': attachments[0].pk,
            'name': 'attachment1.jpeg',
            'extension': 'jpeg',
            'url': (
                'https://api.greenbudget.com'
                '/media/users/1/attachments/attachment1.jpeg'
            )
        },
        {
            'id': attachments[1].pk,
            'name': 'attachment2.jpeg',
            'extension': 'jpeg',
            'url': (
                'https://api.greenbudget.com'
                '/media/users/1/attachments/attachment2.jpeg'
            )
        },
        {
            'id': additional_attachment.pk,
            'name': 'attachment3.jpeg',
            'extension': 'jpeg',
            'url': (
                'https://api.greenbudget.com'
                '/media/users/1/attachments/attachment3.jpeg'
            )
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
@override_settings(APP_URL="https://api.greenbudget.com")
def test_upload_attachment(api_client, user, create_contact, create_attachment,
        test_uploaded_file, models):
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg')
    ]
    contact = create_contact(attachments=attachments)
    uploaded_file = test_uploaded_file('test.jpeg')
    api_client.force_login(user)
    response = api_client.post(
        "/v1/contacts/%s/attachments/" % contact.pk,
        data={'file': uploaded_file}
    )

    assert response.status_code == 200

    contact.refresh_from_db()
    assert contact.attachments.count() == 3

    assert models.Attachment.objects.count() == 3
    assert response.json() == {
        'id': 3,
        'name': 'test.jpeg',
        'extension': 'jpeg',
        'size': 823,
        'url': (
            'https://api.greenbudget.com/'
            'media/users/1/attachments/test.jpeg'
        )
    }
