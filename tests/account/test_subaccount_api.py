import datetime
import pytest


@pytest.mark.freeze_time('2020-01-03')
def test_get_account_subaccounts(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    another_account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 1)
        ),
        budget_f.create_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 2)
        ),
        budget_f.create_subaccount(parent=another_account)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
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
            "order": "t",
        }
    ]
    if budget_f.context == 'budget':
        for r in response_data:
            r.update(contact=None, attachments=[])

    assert response.json()['data'] == response_data


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_subaccount(api_client, user, budget_f, models):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    api_client.force_login(user)
    response = api_client.post(
         "/v1/accounts/%s/subaccounts/" % account.pk, data={
             'identifier': '100',
             'description': 'Test'
         })
    assert response.status_code == 201
    subaccount = models.SubAccount.objects.first()
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
        "order": "n",
        "siblings": [],
        "ancestors": [
            {
                "type": "budget",
                "domain": budget_f.context,
                "id": budget.pk,
                "name": budget.name
            },
            {
                "type": "account",
                "id": account.pk,
                "identifier": account.identifier,
                "description": account.description
            }
        ]
    }
    if budget_f.context == 'budget':
        response_data.update(contact=None, attachments=[])


@pytest.mark.freeze_time('2020-01-01')
def test_get_community_template_account_subaccounts(api_client, user,
        staff_user, create_template, create_template_account,
        create_template_subaccount):
    template = create_template(community=True, created_by=staff_user)
    account = create_template_account(parent=template)
    [
        create_template_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 1)
        ),
        create_template_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 2)
        )
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 403


@pytest.mark.freeze_time('2020-01-01')
def test_get_another_users_community_template_account_subaccounts(api_client,
        create_user, staff_user, create_template, create_template_account,
        create_template_subaccount):
    user = create_user(is_staff=True)
    template = create_template(community=True, created_by=user)
    account = create_template_account(parent=template)
    [
        create_template_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 1)
        ),
        create_template_subaccount(
            parent=account,
            created_at=datetime.datetime(2020, 1, 2)
        )
    ]
    api_client.force_login(staff_user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
