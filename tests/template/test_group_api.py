import pytest

from greenbudget.app.group.models import TemplateAccountGroup


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_account_group(api_client, user, create_template,
        create_template_account):
    template = create_template()
    account = create_template_account(budget=template)

    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/groups/" % template.pk, data={
        'name': 'Group Name',
        'children': [account.pk],
        'color': '#a1887f'
    })
    assert response.status_code == 201

    group = TemplateAccountGroup.objects.first()
    assert group is not None
    assert group.name == "Group Name"
    assert group.children.count() == 1
    assert group.children.first() == account
    assert group.parent == template

    assert response.json() == {
        "id": group.pk,
        "name": "Group Name",
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": '#a1887f',
        "updated_by": None,
        "estimated": None,
        "created_by": user.pk,
        "children": [account.pk]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_account_group_invalid_child(api_client, user,
        create_template_account, create_template):
    template = create_template()
    another_template = create_template()
    # We are trying to create the grouping under `template` but including
    # children that belong to `another_template`, which should trigger a 400
    # response.
    account = create_template_account(budget=another_template)

    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/groups/" % template.pk, data={
        'name': 'Group Name',
        'children': [account.pk],
        'color': '#a1887f',
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_account_group_duplicate_name(api_client, user,
        create_template_account, create_template,
        create_template_account_group):
    template = create_template()
    account = create_template_account(budget=template)
    create_template_account_group(name="Group Name", parent=template)

    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/groups/" % template.pk, data={
        'name': 'Group Name',
        'children': [account.pk],
        'color': '#a1887f'
    })
    assert response.status_code == 400