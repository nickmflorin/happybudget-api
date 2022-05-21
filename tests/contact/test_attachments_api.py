import os
import pytest

from django.test import override_settings


@pytest.mark.freeze_time('2020-01-01')
@override_settings(APP_URL="https://api.happybudget.com")
def test_attachments_properly_serializes(api_client, user, f):
    attachments = [
        f.create_attachment(name='attachment1.jpeg'),
        f.create_attachment(name='attachment2.jpeg')
    ]
    contact = f.create_contact(attachments=attachments)
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
                'https://api.happybudget.com'
                '/media/users/1/attachments/attachment1.jpeg'
            )
        },
        {
            'id': attachments[1].pk,
            'name': 'attachment2.jpeg',
            'extension': 'jpeg',
            'url': (
                'https://api.happybudget.com'
                '/media/users/1/attachments/attachment2.jpeg'
            )
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
@override_settings(APP_URL="https://api.happybudget.com")
def test_get_attachments(api_client, user, f):
    attachments = [
        f.create_attachment(name='attachment1.jpeg'),
        f.create_attachment(name='attachment2.jpeg')
    ]
    contact = f.create_contact(attachments=attachments)
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
                'https://api.happybudget.com/'
                'media/users/1/attachments/attachment1.jpeg'
            )
        },
        {
            'id': attachments[1].pk,
            'name': 'attachment2.jpeg',
            'extension': 'jpeg',
            'size': 823,
            'url': (
                'https://api.happybudget.com/'
                'media/users/1/attachments/attachment2.jpeg'
            )
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
@override_settings(APP_URL="https://api.happybudget.com")
def test_get_attachments_file_not_found_locally(api_client, user, f):
    # Note: We do not need to test if the file is not found remotely in AWS
    # because the SimpleAttachmentSerializer, which is used for the list
    # endpoint, only references the extension - and the extension can still be
    # determined if the file does not exist since it is solely based on the name,
    # which is stored on the DB field.
    attachments = [
        f.create_attachment(name='attachment1.jpeg'),
        f.create_attachment(name='attachment2.jpeg')
    ]
    contact = f.create_contact(attachments=attachments)
    os.remove(attachments[0].file.path)

    api_client.force_login(user)
    response = api_client.get("/v1/contacts/%s/attachments/" % contact.pk)
    # Instead of causing a 500 error, the attachment associated with a file that
    # cannot be found should simply be excluded.
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [
        {
            'id': attachments[1].pk,
            'name': 'attachment2.jpeg',
            'extension': 'jpeg',
            'size': 823,
            'url': (
                'https://api.happybudget.com/'
                'media/users/1/attachments/attachment2.jpeg'
            )
        }
    ]


def test_delete_attachment(api_client, user, f):
    attachments = [
        f.create_attachment(name='attachment1.jpeg'),
        f.create_attachment(name='attachment2.jpeg')
    ]
    contact = f.create_contact(attachments=attachments)
    api_client.force_login(user)
    response = api_client.delete("/v1/contacts/%s/attachments/%s/" % (
        contact.pk, attachments[0].pk))
    assert response.status_code == 204
    assert contact.attachments.count() == 1


@pytest.mark.freeze_time('2020-01-01')
@override_settings(APP_URL="https://api.happybudget.com")
def test_update_attachments(api_client, user, f):
    attachments = [
        f.create_attachment(name='attachment1.jpeg'),
        f.create_attachment(name='attachment2.jpeg')
    ]
    contact = f.create_contact(attachments=attachments)
    additional_attachment = f.create_attachment(name='attachment3.jpeg')
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
                'https://api.happybudget.com'
                '/media/users/1/attachments/attachment1.jpeg'
            )
        },
        {
            'id': attachments[1].pk,
            'name': 'attachment2.jpeg',
            'extension': 'jpeg',
            'url': (
                'https://api.happybudget.com'
                '/media/users/1/attachments/attachment2.jpeg'
            )
        },
        {
            'id': additional_attachment.pk,
            'name': 'attachment3.jpeg',
            'extension': 'jpeg',
            'url': (
                'https://api.happybudget.com'
                '/media/users/1/attachments/attachment3.jpeg'
            )
        }
    ]


@override_settings(APP_URL="https://api.happybudget.com")
def test_upload_attachment(api_client, user, f, test_uploaded_file, models):
    attachments = [
        f.create_attachment(name='attachment1.jpeg'),
        f.create_attachment(name='attachment2.jpeg')
    ]
    contact = f.create_contact(attachments=attachments)
    uploaded_file = test_uploaded_file('test.jpeg')
    api_client.force_login(user)
    response = api_client.post(
        "/v1/contacts/%s/attachments/" % contact.pk,
        data={'file': uploaded_file}
    )

    assert response.status_code == 201

    contact.refresh_from_db()
    assert contact.attachments.count() == 3

    assert models.Attachment.objects.count() == 3
    assert response.json()['data'] == [{
        'id': 3,
        'name': 'test.jpeg',
        'extension': 'jpeg',
        'size': 823,
        'url': (
            'https://api.happybudget.com/'
            'media/users/1/attachments/test.jpeg'
        )
    }]


@override_settings(APP_URL="https://api.happybudget.com")
def test_upload_multiple_attachments(api_client, user, f, models,
        test_uploaded_file):
    attachments = [
        f.create_attachment(name='attachment1.jpeg'),
        f.create_attachment(name='attachment2.jpeg')
    ]
    contact = f.create_contact(attachments=attachments)
    uploaded_files = [
        test_uploaded_file('test1.jpeg'),
        test_uploaded_file('test2.jpeg')
    ]
    api_client.force_login(user)
    response = api_client.post(
        "/v1/contacts/%s/attachments/" % contact.pk,
        data={'files': uploaded_files}
    )

    assert response.status_code == 201

    contact.refresh_from_db()
    assert contact.attachments.count() == 4

    assert models.Attachment.objects.count() == 4
    assert response.json()['data'] == [
        {
            'id': 3,
            'name': 'test1.jpeg',
            'extension': 'jpeg',
            'size': 823,
            'url': (
                'https://api.happybudget.com/'
                'media/users/1/attachments/test1.jpeg'
            )
        },
        {
            'id': 4,
            'name': 'test2.jpeg',
            'extension': 'jpeg',
            'size': 823,
            'url': (
                'https://api.happybudget.com/'
                'media/users/1/attachments/test2.jpeg'
            )
        }
    ]
