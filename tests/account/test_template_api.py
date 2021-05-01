import pytest

from greenbudget.app.account.models import TemplateAccount


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_accounts(api_client, user, create_template_account,
        create_template):
    template = create_template()
    accounts = [
        create_template_account(budget=template),
        create_template_account(budget=template)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/templates/%s/accounts/" % template.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": accounts[0].pk,
            "identifier": "%s" % accounts[0].identifier,
            "description": accounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "budget": template.pk,
            "type": "account",
            "estimated": None,
            "subaccounts": [],
            "group": None,
            "created_by": user.pk,
            "updated_by": user.pk,
            "ancestors": [{
                "type": "template",
                "id": template.pk,
                "name": template.name,
            }],
            "siblings": [{
                "type": "account",
                "id": accounts[1].pk,
                "identifier": accounts[1].identifier,
                "description": accounts[1].description
            }]
        },
        {
            "id": accounts[1].pk,
            "identifier": "%s" % accounts[1].identifier,
            "description": accounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "budget": template.pk,
            "type": "account",
            "estimated": None,
            "subaccounts": [],
            "group": None,
            "created_by": user.pk,
            "updated_by": user.pk,
            "ancestors": [{
                "type": "template",
                "id": template.pk,
                "name": template.name
            }],
            "siblings": [{
                "type": "account",
                "id": accounts[0].pk,
                "identifier": accounts[0].identifier,
                "description": accounts[0].description
            }]
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_community_template_accounts(api_client, user, staff_user,
        create_template_account, create_template):
    template = create_template(community=True, created_by=staff_user)
    [
        create_template_account(budget=template),
        create_template_account(budget=template)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/templates/%s/accounts/" % template.pk)
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_get_another_users_community_template_accounts(api_client, staff_user,
        create_template_account, create_template, create_user):
    user = create_user(is_staff=True)
    template = create_template(created_by=user, community=True)
    [
        create_template_account(budget=template),
        create_template_account(budget=template)
    ]
    api_client.force_login(staff_user)
    response = api_client.get("/v1/templates/%s/accounts/" % template.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2


@ pytest.mark.freeze_time('2020-01-01')
def test_create_template_account(api_client, user, create_template):
    template = create_template()
    api_client.force_login(user)
    response = api_client.post(
        "/v1/templates/%s/accounts/" % template.pk, data={
            'identifier': 'new_account'
        })
    assert response.status_code == 201

    account = TemplateAccount.objects.first()
    assert account is not None

    assert response.json() == {
        "id": account.pk,
        "identifier": 'new_account',
        "description": None,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "budget": template.pk,
        "type": "account",
        "estimated": None,
        "subaccounts": [],
        "group": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "siblings": [],
        "ancestors": [{
            "type": "template",
            "id": template.pk,
            "name": template.name
        }]
    }
