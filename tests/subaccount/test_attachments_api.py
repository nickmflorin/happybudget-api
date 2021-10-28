import pytest

from django.test import override_settings


@pytest.mark.freeze_time('2020-01-01')
@override_settings(APP_URL="https://api.greenbudget.com")
def test_attachments_properly_serialize(api_client, user, create_budget_account,
        create_budget_subaccount, create_budget, create_attachment):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg')
    ]
    subaccount = create_budget_subaccount(
        parent=account,
        attachments=attachments
    )
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
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
def test_get_attachments(api_client, user, create_budget_account,
        create_budget_subaccount, create_budget, create_attachment):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg')
    ]
    subaccount = create_budget_subaccount(
        parent=account,
        attachments=attachments
    )
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/attachments/" % subaccount.pk)
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
def test_delete_attachment(api_client, user, create_budget_account,
        create_budget_subaccount, create_budget, create_attachment):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg')
    ]
    subaccount = create_budget_subaccount(
        parent=account,
        attachments=attachments
    )
    api_client.force_login(user)
    response = api_client.delete("/v1/subaccounts/%s/attachments/%s/" % (
        subaccount.pk, attachments[0].pk))
    assert response.status_code == 204
    assert subaccount.attachments.count() == 1


@pytest.mark.freeze_time('2020-01-01')
@override_settings(APP_URL="https://api.greenbudget.com")
def test_update_attachments(api_client, user, create_budget_account,
        create_budget_subaccount, create_budget, create_attachment):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg')
    ]
    subaccount = create_budget_subaccount(
        parent=account,
        attachments=attachments
    )
    additional_attachment = create_attachment(name='attachment3.jpeg')
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        'attachments': [a.pk for a in attachments] + [additional_attachment.pk]
    })
    assert response.status_code == 200

    subaccount.refresh_from_db()
    assert subaccount.attachments.count() == 3

    assert 'attachments' in response.json()
    assert response.json()['attachments'] == [
        {
            'id': attachments[0].pk,
            'name': 'attachment1.jpeg',
            'extension': 'jpeg',
            'url': (
                'https://api.greenbudget.com/'
                'media/users/1/attachments/attachment1.jpeg'
            )
        },
        {
            'id': attachments[1].pk,
            'name': 'attachment2.jpeg',
            'extension': 'jpeg',
            'url': (
                'https://api.greenbudget.com/'
                'media/users/1/attachments/attachment2.jpeg'
            )
        },
        {
            'id': additional_attachment.pk,
            'name': 'attachment3.jpeg',
            'extension': 'jpeg',
            'url': (
                'https://api.greenbudget.com/'
                'media/users/1/attachments/attachment3.jpeg'
            )
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
@override_settings(APP_URL="https://api.greenbudget.com")
def test_upload_attachment(api_client, user, create_budget_account,
        create_budget_subaccount, create_budget, create_attachment,
        test_uploaded_file, models):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    attachments = [
        create_attachment(name='attachment1.jpeg'),
        create_attachment(name='attachment2.jpeg')
    ]
    subaccount = create_budget_subaccount(
        parent=account,
        attachments=attachments
    )
    uploaded_file = test_uploaded_file('test.jpeg')
    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/attachments/" % subaccount.pk,
        data={'file': uploaded_file}
    )

    assert response.status_code == 200

    subaccount.refresh_from_db()
    assert subaccount.attachments.count() == 3

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
