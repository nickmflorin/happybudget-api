import pytest

from greenbudget.app.account.models import TemplateAccount
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.template.models import Template


@pytest.mark.freeze_time('2020-01-01')
def test_get_templates(api_client, user, create_template):
    api_client.force_login(user)
    templates = [create_template(), create_template()]
    response = api_client.get("/v1/templates/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": templates[0].pk,
            "name": templates[0].name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "estimated": None,
            'trash': False,
            "type": "template",
            "created_by": user.pk,
            "image": None,
        },
        {
            "id": templates[1].pk,
            "name": templates[1].name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "estimated": None,
            'trash': False,
            "type": "template",
            "created_by": user.pk,
            "image": None,
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
        "trash": False,
        "estimated": None,
        "type": "template",
        "created_by": user.pk,
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_template(api_client, user):
    api_client.force_login(user)
    response = api_client.post("/v1/templates/", data={
        "name": "Test Name",
    })
    assert response.status_code == 201

    template = Template.objects.first()
    assert template is not None
    assert template.name == "Test Name"
    assert response.json() == {
        "id": template.pk,
        "name": "Test Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        'trash': False,
        "estimated": None,
        "type": "template",
        "created_by": user.pk,
        "image": None,
    }


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
        'trash': False,
        "estimated": None,
        "type": "template",
        "created_by": user.pk,
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_templates_in_trash(api_client, user, create_template):
    api_client.force_login(user)
    templates = [
        create_template(trash=True),
        create_template(trash=True),
        create_template()
    ]
    response = api_client.get("/v1/templates/trash/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": templates[0].pk,
            "name": templates[0].name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            'trash': True,
            "estimated": None,
            "type": "template",
            "created_by": user.pk,
            "image": None,
        },
        {
            "id": templates[1].pk,
            "name": templates[1].name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            'trash': True,
            "estimated": None,
            "type": "template",
            "created_by": user.pk,
            "image": None,
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_in_trash(api_client, user, create_template):
    api_client.force_login(user)
    template = create_template(trash=True)
    response = api_client.get("/v1/templates/trash/%s/" % template.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": template.pk,
        "name": template.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        'trash': True,
        "estimated": None,
        "type": "template",
        "created_by": user.pk,
        "image": None,
    }


def test_delete_template(api_client, user, create_template):
    api_client.force_login(user)
    template = create_template()
    response = api_client.delete("/v1/templates/%s/" % template.pk)
    assert response.status_code == 204

    template.refresh_from_db()
    assert template.trash is True
    assert template.id is not None


def test_restore_template(api_client, user, create_template):
    api_client.force_login(user)
    template = create_template(trash=True)
    response = api_client.patch("/v1/templates/trash/%s/restore/" % template.pk)
    assert response.status_code == 201

    assert response.json()['id'] == template.pk
    assert response.json()['trash'] is False

    template.refresh_from_db()
    assert template.trash is False


def test_permanently_delete_template(api_client, user, create_template):
    api_client.force_login(user)
    template = create_template(trash=True)
    response = api_client.delete("/v1/templates/trash/%s/" % template.pk)
    assert response.status_code == 204
    assert Template.objects.first() is None


def test_bulk_update_template_accounts(api_client, user, create_template,
        create_template_account):
    api_client.force_login(user)
    template = create_template()
    accounts = [
        create_template_account(budget=template),
        create_template_account(budget=template)
    ]
    response = api_client.patch(
        "/v1/templates/%s/bulk-update-accounts/" % template.pk,
        format='json',
        data={
            'data': [
                {
                    'id': accounts[0].pk,
                    'description': 'New Description 1',
                },
                {
                    'id': accounts[1].pk,
                    'description': 'New Description 2',
                }
            ]
        })
    assert response.status_code == 200

    accounts[0].refresh_from_db()
    assert accounts[0].description == "New Description 1"
    accounts[1].refresh_from_db()
    assert accounts[1].description == "New Description 2"


def test_bulk_update_template_accounts_outside_template(api_client, user,
        create_template, create_template_account):
    api_client.force_login(user)
    template = create_template()
    another_template = create_template()
    accounts = [
        create_template_account(budget=template),
        create_template_account(budget=another_template)
    ]
    response = api_client.patch(
        "/v1/templates/%s/bulk-update-accounts/" % template.pk,
        format='json',
        data={
            'data': [
                {
                    'id': accounts[0].pk,
                    'description': 'New Description 1',
                },
                {
                    'id': accounts[1].pk,
                    'description': 'New Description 2',
                }
            ]
        })
    assert response.status_code == 400


def test_bulk_create_template_accounts(api_client, user, create_template):
    api_client.force_login(user)
    template = create_template()
    response = api_client.patch(
        "/v1/templates/%s/bulk-create-accounts/" % template.pk,
        format='json',
        data={
            'data': [
                {
                    'identifier': 'account-a',
                    'description': 'New Description 1',
                },
                {
                    'identifier': 'account-b',
                    'description': 'New Description 2',
                }
            ]
        })
    assert response.status_code == 201

    accounts = TemplateAccount.objects.all()
    assert len(accounts) == 2
    assert accounts[0].identifier == "account-a"
    assert accounts[0].description == "New Description 1"
    assert accounts[0].budget == template
    assert accounts[1].description == "New Description 2"
    assert accounts[1].identifier == "account-b"
    assert accounts[1].budget == template

    assert response.json()['data'][0]['identifier'] == 'account-a'
    assert response.json()['data'][0]['description'] == 'New Description 1'
    assert response.json()['data'][1]['identifier'] == 'account-b'
    assert response.json()['data'][1]['description'] == 'New Description 2'


@pytest.mark.freeze_time('2020-01-01')
def test_bulk_create_template_fringes(api_client, user, create_template):
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

    fringes = Fringe.objects.all()
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


def test_bulk_update_template_fringes_name_not_unique(api_client, user,
        create_template, create_fringe):
    api_client.force_login(user)
    template = create_template()
    create_fringe(budget=template, name='Non-Unique Name')
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
                    'name': 'Non-Unique Name',
                }
            ]
        })
    assert response.status_code == 400


def test_bulk_update_template_fringes_name_not_unique_in_update(api_client,
        user, create_template, create_fringe):
    api_client.force_login(user)
    template = create_template()
    fringes = [
        create_fringe(budget=template, name='Non-Unique Name'),
        create_fringe(budget=template)
    ]
    response = api_client.patch(
        "/v1/templates/%s/bulk-update-fringes/" % template.pk,
        format='json',
        data={
            'data': [
                {
                    'id': fringes[0].pk,
                    'rate': 5.1,
                },
                {
                    'id': fringes[1].pk,
                    'name': 'Non-Unique Name',
                }
            ]
        })
    assert response.status_code == 400


def test_bulk_update_template_fringes_name_will_be_unique(api_client, user,
        create_template, create_fringe):
    api_client.force_login(user)
    template = create_template()
    fringes = [
        create_fringe(budget=template, name='Non-Unique Name'),
        create_fringe(budget=template)
    ]
    response = api_client.patch(
        "/v1/templates/%s/bulk-update-fringes/" % template.pk,
        format='json',
        data={
            'data': [
                {
                    'id': fringes[0].pk,
                    'name': 'New Name',
                },
                {
                    'id': fringes[1].pk,
                    'name': 'Non-Unique Name',
                }
            ]
        })
    assert response.status_code == 200
