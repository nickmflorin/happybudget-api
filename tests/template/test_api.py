import pytest

from greenbudget.app.account.models import TemplateAccount
from greenbudget.app.fringe.models import Fringe
from greenbudget.app.template.models import Template


@pytest.mark.freeze_time('2020-01-01')
def test_get_templates(api_client, user, create_template, staff_user):
    api_client.force_login(user)
    templates = [
        create_template(),
        create_template(),
        create_template(community=True, created_by=staff_user),
        create_template(community=True, created_by=staff_user)
    ]
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
            "type": "template",
            "created_by": user.pk,
            "image": None,
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_staff_user_templates(api_client, create_template, staff_user):
    api_client.force_login(staff_user)
    templates = [
        create_template(created_by=staff_user),
        create_template(created_by=staff_user),
        create_template(community=True, created_by=staff_user),
        create_template(community=True, created_by=staff_user)
    ]
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
            "type": "template",
            "created_by": staff_user.pk,
            "image": None,
        },
        {
            "id": templates[1].pk,
            "name": templates[1].name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "estimated": None,
            "type": "template",
            "created_by": staff_user.pk,
            "image": None,
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_community_templates(api_client, user, create_template, staff_user):
    api_client.force_login(user)
    templates = [
        create_template(community=True, created_by=staff_user),
        create_template(community=True, created_by=staff_user),
        create_template()
    ]
    response = api_client.get("/v1/templates/community/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": templates[0].pk,
            "name": templates[0].name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "estimated": None,
            "type": "template",
            "created_by": staff_user.pk,
            "image": None,
        },
        {
            "id": templates[1].pk,
            "name": templates[1].name,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "estimated": None,
            "type": "template",
            "created_by": staff_user.pk,
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
        "estimated": None,
        "type": "template",
        "created_by": user.pk,
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_another_user_template(api_client, user, create_template,
        create_user):
    another_user = create_user()
    api_client.force_login(user)
    template = create_template(created_by=another_user)
    response = api_client.get("/v1/templates/%s/" % template.pk)
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_get_community_template(api_client, staff_user, create_template,
        create_user):
    another_staff_user = create_user(is_staff=True)
    api_client.force_login(staff_user)
    template = create_template(community=True, created_by=another_staff_user)
    response = api_client.get("/v1/templates/%s/" % template.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": template.pk,
        "name": template.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "estimated": None,
        "type": "template",
        "created_by": another_staff_user.pk,
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_community_template_non_staff_user(api_client, staff_user, user,
        create_template):
    api_client.force_login(user)
    template = create_template(community=True, created_by=staff_user)
    response = api_client.get("/v1/templates/%s/" % template.pk)
    assert response.status_code == 403


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
        "estimated": None,
        "type": "template",
        "created_by": user.pk,
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_community_template(api_client, staff_user):
    api_client.force_login(staff_user)
    response = api_client.post("/v1/templates/community/", data={
        "name": "Test Name",
    })
    assert response.status_code == 201

    template = Template.objects.first()
    assert template is not None
    assert template.name == "Test Name"
    assert template.community is True
    assert response.json() == {
        "id": template.pk,
        "name": "Test Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "estimated": None,
        "type": "template",
        "created_by": staff_user.pk,
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_community_template_non_staff_user(api_client, user):
    api_client.force_login(user)
    response = api_client.post("/v1/templates/community/", data={
        "name": "Test Name",
    })
    assert response.status_code == 403


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
        "estimated": None,
        "type": "template",
        "created_by": user.pk,
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_community_template(api_client, staff_user, create_template):
    template = create_template(created_by=staff_user, community=True)
    api_client.force_login(staff_user)
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
        "estimated": None,
        "type": "template",
        "created_by": staff_user.pk,
        "image": None,
    }


@pytest.mark.freeze_time('2020-01-01')
def test_make_template_community(api_client, staff_user, create_template):
    template = create_template(created_by=staff_user)
    api_client.force_login(staff_user)
    response = api_client.patch("/v1/templates/%s/" % template.pk, data={
         "community": True
    })
    assert response.status_code == 200
    template.refresh_from_db()
    assert template.community is True


@pytest.mark.freeze_time('2020-01-01')
def test_make_template_community_requires_staff(api_client, staff_user, user,
        create_template):
    template = create_template(created_by=staff_user)
    api_client.force_login(user)
    response = api_client.patch("/v1/templates/%s/" % template.pk, data={
         "community": True
    })
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_update_community_template_non_staff_user(api_client, staff_user,
        create_template, user):
    template = create_template(created_by=staff_user, community=True)
    api_client.force_login(user)
    response = api_client.patch("/v1/templates/%s/" % template.pk, data={
         "name": "New Name"
    })
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_duplicate_template(api_client, user, create_template,
        create_template_account, create_template_subaccount,
        create_fringe, create_template_account_group,
        create_template_subaccount_group):
    original = create_template(created_by=user)
    fringes = [
        create_fringe(
            budget=original,
            created_by=user,
            updated_by=user
        ),
        create_fringe(
            budget=original,
            created_by=user,
            updated_by=user
        ),
    ]
    account_group = create_template_account_group(parent=original)
    accounts = [
        create_template_account(
            budget=original,
            created_by=user,
            updated_by=user,
            group=account_group,
        ),
        create_template_account(
            budget=original,
            created_by=user,
            updated_by=user,
            group=account_group,
        )
    ]
    subaccount_group = create_template_subaccount_group(parent=accounts[0])
    subaccounts = [
        create_template_subaccount(
            parent=accounts[0],
            budget=original,
            created_by=user,
            updated_by=user,
            group=subaccount_group
        ),
        create_template_subaccount(
            parent=accounts[1],
            budget=original,
            created_by=user,
            updated_by=user
        )
    ]
    child_subaccounts = [
        create_template_subaccount(
            parent=subaccounts[0],
            budget=original,
            created_by=user,
            updated_by=user
        ),
        create_template_subaccount(
            parent=subaccounts[1],
            budget=original,
            created_by=user,
            updated_by=user
        )
    ]
    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/duplicate/" % original.pk)
    assert Template.objects.count() == 2
    template = Template.objects.all()[1]

    assert response.status_code == 201
    assert response.json() == {
        "id": template.pk,
        "name": original.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "estimated": None,
        "type": "template",
        "created_by": user.pk,
        "image": None,
    }

    assert template.name == original.name
    assert template.accounts.count() == 2
    assert template.created_by == user

    assert template.groups.count() == 1
    budget_account_group = template.groups.first()
    assert budget_account_group.name == account_group.name
    assert budget_account_group.color == account_group.color

    assert template.fringes.count() == 2

    first_fringe = template.fringes.first()
    assert first_fringe.created_by == user
    assert first_fringe.updated_by == user
    assert first_fringe.name == fringes[0].name
    assert first_fringe.description == fringes[0].description
    assert first_fringe.cutoff == fringes[0].cutoff
    assert first_fringe.rate == fringes[0].rate
    assert first_fringe.unit == fringes[0].unit

    second_fringe = template.fringes.all()[1]
    assert second_fringe.created_by == user
    assert second_fringe.updated_by == user
    assert second_fringe.name == fringes[1].name
    assert second_fringe.description == fringes[1].description
    assert second_fringe.cutoff == fringes[1].cutoff
    assert second_fringe.rate == fringes[1].rate
    assert second_fringe.unit == fringes[1].unit

    assert template.accounts.count() == 2

    first_account = template.accounts.first()
    assert first_account.group == budget_account_group
    assert first_account.identifier == accounts[0].identifier
    assert first_account.description == accounts[0].description
    assert first_account.created_by == user
    assert first_account.updated_by == user

    assert first_account.subaccounts.count() == 1

    assert first_account.groups.count() == 1
    budget_subaccount_group = first_account.groups.first()
    assert budget_subaccount_group.name == subaccount_group.name
    assert budget_subaccount_group.color == subaccount_group.color

    first_account_subaccount = first_account.subaccounts.first()
    assert first_account_subaccount.group == budget_subaccount_group

    assert first_account_subaccount.created_by == user
    assert first_account_subaccount.updated_by == user
    assert first_account_subaccount.identifier == subaccounts[0].identifier
    assert first_account_subaccount.description == subaccounts[0].description
    assert first_account_subaccount.budget == template
    # These values will be None because the subaccount has children.
    assert first_account_subaccount.name is None
    assert first_account_subaccount.rate is None
    assert first_account_subaccount.quantity is None
    assert first_account_subaccount.multiplier is None
    assert first_account_subaccount.unit is None

    assert first_account_subaccount.subaccounts.count() == 1
    first_account_subaccount_subaccount = first_account_subaccount.subaccounts.first()  # noqa
    assert first_account_subaccount_subaccount.created_by == user
    assert first_account_subaccount_subaccount.updated_by == user
    assert first_account_subaccount_subaccount.identifier == child_subaccounts[0].identifier  # noqa
    assert first_account_subaccount_subaccount.description == child_subaccounts[0].description  # noqa
    assert first_account_subaccount_subaccount.name == child_subaccounts[0].name  # noqa
    assert first_account_subaccount_subaccount.rate == child_subaccounts[0].rate  # noqa
    assert first_account_subaccount_subaccount.quantity == child_subaccounts[0].quantity  # noqa
    assert first_account_subaccount_subaccount.multiplier == child_subaccounts[0].multiplier  # noqa
    assert first_account_subaccount_subaccount.unit == child_subaccounts[0].unit  # noqa
    assert first_account_subaccount_subaccount.budget == template

    second_account = template.accounts.all()[1]
    assert second_account.group == budget_account_group
    assert second_account.identifier == accounts[1].identifier
    assert second_account.description == accounts[1].description
    assert second_account.created_by == user
    assert second_account.updated_by == user

    assert second_account.subaccounts.count() == 1
    second_account_subaccount = second_account.subaccounts.first()
    assert second_account_subaccount.created_by == user
    assert second_account_subaccount.updated_by == user
    assert second_account_subaccount.identifier == subaccounts[1].identifier
    assert second_account_subaccount.description == subaccounts[1].description
    assert second_account_subaccount.budget == template
    # These values will be None because the subaccount has children.
    assert second_account_subaccount.name is None
    assert second_account_subaccount.rate is None
    assert second_account_subaccount.quantity is None
    assert second_account_subaccount.multiplier is None
    assert second_account_subaccount.unit is None

    assert second_account_subaccount.subaccounts.count() == 1
    second_account_subaccount_subaccount = second_account_subaccount.subaccounts.first()  # noqa
    assert second_account_subaccount_subaccount.created_by == user
    assert second_account_subaccount_subaccount.updated_by == user
    assert second_account_subaccount_subaccount.identifier == child_subaccounts[1].identifier  # noqa
    assert second_account_subaccount_subaccount.description == child_subaccounts[1].description  # noqa
    assert second_account_subaccount_subaccount.name == child_subaccounts[1].name  # noqa
    assert second_account_subaccount_subaccount.rate == child_subaccounts[1].rate  # noqa
    assert second_account_subaccount_subaccount.quantity == child_subaccounts[1].quantity  # noqa
    assert second_account_subaccount_subaccount.multiplier == child_subaccounts[1].multiplier  # noqa
    assert second_account_subaccount_subaccount.unit == child_subaccounts[1].unit  # noqa
    assert second_account_subaccount_subaccount.budget == template


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


def test_delete_community_template(api_client, staff_user, create_template):
    api_client.force_login(staff_user)
    template = create_template(created_by=staff_user, community=True)
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
