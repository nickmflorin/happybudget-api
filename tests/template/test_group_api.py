import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_account_groups(api_client, user, create_template,
        create_template_account, create_template_account_group):
    template = create_template()
    group = create_template_account_group(parent=template)
    account = create_template_account(budget=template, group=group)
    api_client.force_login(user)
    response = api_client.get("/v1/templates/%s/groups/" % template.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'] == [{
        "id": group.pk,
        "name": group.name,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "color": group.color,
        "updated_by": user.pk,
        "estimated": 0.0,
        "created_by": user.pk,
        "children": [account.pk]
    }]


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_account_group(api_client, user, create_template,
        create_template_account, models):
    template = create_template()
    account = create_template_account(budget=template)

    api_client.force_login(user)
    response = api_client.post("/v1/templates/%s/groups/" % template.pk, data={
        'name': 'Group Name',
        'children': [account.pk],
        'color': '#a1887f'
    })
    assert response.status_code == 201

    group = models.TemplateAccountGroup.objects.first()
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
        "updated_by": user.pk,
        "estimated": 0.0,
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
