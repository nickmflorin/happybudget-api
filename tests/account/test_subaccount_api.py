import datetime


def test_get_account_children(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    another_account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 1).replace(
                tzinfo=datetime.timezone.utc)
        ),
        budget_f.create_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 2).replace(
                tzinfo=datetime.timezone.utc)
        ),
        budget_f.create_subaccount(parent=another_account)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response_data = [
        {
            "id": subaccounts[0].pk,
            "identifier": "%s" % subaccounts[0].identifier,
            "description": subaccounts[0].description,
            "quantity": subaccounts[0].quantity,
            "rate": subaccounts[0].rate,
            "multiplier": subaccounts[0].multiplier,
            "type": "subaccount",
            "object_id": account.pk,
            "parent_type": "account",
            "nominal_value": 0.0,
            "fringe_contribution": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "fringes": [],
            "unit": None,
            "domain": budget_f.domain,
            "order": "n",
        },
        {
            "id": subaccounts[1].pk,
            "identifier": "%s" % subaccounts[1].identifier,
            "description": subaccounts[1].description,
            "quantity": subaccounts[1].quantity,
            "rate": subaccounts[1].rate,
            "multiplier": subaccounts[1].multiplier,
            "type": "subaccount",
            "object_id": account.pk,
            "parent_type": "account",
            "nominal_value": 0.0,
            "fringe_contribution": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "fringes": [],
            "unit": None,
            "domain": budget_f.domain,
            "order": "t",
        }
    ]
    if budget_f.domain == 'budget':
        for r in response_data:
            r.update(contact=None, attachments=[])

    assert response.json()['data'] == response_data


def test_get_account_children_ordered_by_group(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    groups = [
        f.create_group(parent=account),
        f.create_group(parent=account)
    ]
    # pylint: disable=expression-not-assigned
    [
        budget_f.create_subaccount(parent=account, group=groups[1], order="n"),
        budget_f.create_subaccount(parent=account, order="t"),
        budget_f.create_subaccount(parent=account, group=groups[0], order="w"),
        budget_f.create_subaccount(parent=account, group=groups[1], order="y"),
        budget_f.create_subaccount(parent=account, group=groups[0], order="yn"),
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 5
    assert [obj['id'] for obj in response.json()['data']] == [1, 4, 3, 5, 2]


def test_create_budget_subaccount(api_client, user, budget_f, models, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    # Make sure that we can create the SubAccount with a Group.  To do this, the
    # Group must not be empty.
    group = f.create_group(parent=account)
    budget_f.create_subaccount(group=group, parent=account)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/accounts/%s/children/" % account.pk, data={
            'identifier': '100',
            'description': 'Test',
            'group': group.pk
        })
    assert response.status_code == 201
    subaccounts = models.SubAccount.objects.all()
    assert len(subaccounts) == 2
    subaccount = subaccounts[1]

    assert subaccount is not None
    assert subaccount.description == "Test"
    assert subaccount.identifier == "100"

    response_data = {
        "id": subaccount.pk,
        "identifier": '100',
        "description": 'Test',
        "quantity": None,
        "rate": None,
        "multiplier": None,
        "unit": None,
        "type": "subaccount",
        "object_id": account.pk,
        "parent_type": "account",
        "nominal_value": 0.0,
        "fringe_contribution": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "fringes": [],
        "order": "t",
        "table": [
            {
                "type": "subaccount",
                "id": subaccounts[0].pk,
                "identifier": subaccounts[0].identifier,
                "description": subaccounts[0].description,
                "domain": budget_f.domain,
            },
            {
                "type": "subaccount",
                "id": subaccounts[1].pk,
                "identifier": subaccounts[1].identifier,
                "description": subaccounts[1].description,
                "domain": budget_f.domain,
            }
        ],
        "domain": budget_f.domain,
        "ancestors": [
            {
                "type": "budget",
                "domain": budget_f.domain,
                "id": budget.pk,
                "name": budget.name
            },
            {
                "type": "account",
                "id": account.pk,
                "identifier": account.identifier,
                "description": account.description,
                "domain": budget_f.domain,
            }
        ]
    }
    if budget_f.domain == 'budget':
        response_data.update(contact=None, attachments=[])
    assert response.json() == response_data


def test_create_subaccount_group_not_in_table(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    another_account = budget_f.create_account(parent=budget)

    # The group must not be empty.
    group = f.create_group(parent=another_account)
    budget_f.create_subaccount(group=group, parent=another_account)

    api_client.force_login(user)
    response = api_client.post(
        "/v1/accounts/%s/children/" % account.pk,
        data={'identifier': 'new_subaccount', 'group': group.pk}
    )
    assert response.status_code == 400
    assert response.json()['errors'][0]['code'] == 'does_not_exist_in_table'


def test_create_subaccount_group_empty(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = f.create_group(parent=account)
    api_client.force_login(user)
    response = api_client.post(
        "/v1/accounts/%s/children/" % account.pk,
        data={'identifier': 'new_subaccount', 'group': group.pk}
    )
    assert response.status_code == 400
    assert response.json()['errors'][0]['code'] == 'is_empty'


def test_get_community_template_account_children(
        api_client, user, staff_user, f):
    template = f.create_template(community=True, created_by=staff_user)
    account = f.create_template_account(parent=template)
    # pylint: disable=expression-not-assigned
    [
        f.create_template_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 1).replace(
                tzinfo=datetime.timezone.utc)
        ),
        f.create_template_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 2).replace(
                tzinfo=datetime.timezone.utc)
        )
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 403


def test_get_another_users_community_template_account_children(api_client,
        staff_user, f):
    user = f.create_user(is_staff=True)
    template = f.create_template(community=True, created_by=user)
    account = f.create_template_account(parent=template)
    # pylint: disable=expression-not-assigned
    [
        f.create_template_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 1).replace(
                tzinfo=datetime.timezone.utc)
        ),
        f.create_template_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 2).replace(
                tzinfo=datetime.timezone.utc)
        )
    ]
    api_client.force_login(staff_user)
    response = api_client.get("/v1/accounts/%s/children/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
