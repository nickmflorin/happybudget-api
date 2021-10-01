import datetime
import pytest

from greenbudget.app import signals


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_account_subaccounts(api_client, user, create_template,
        create_template_account, create_template_subaccount):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)
        another_account = create_template_account(parent=template)
        subaccounts = [
            create_template_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 1)
            ),
            create_template_subaccount(
                parent=account,
                created_at=datetime.datetime(2020, 1, 2)
            ),
            create_template_subaccount(parent=another_account)
        ]
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": subaccounts[0].pk,
            "identifier": "%s" % subaccounts[0].identifier,
            "description": subaccounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[0].quantity,
            "rate": subaccounts[0].rate,
            "multiplier": subaccounts[0].multiplier,
            "type": "subaccount",
            "object_id": account.pk,
            "parent_type": "account",
            "nominal_value": 0.0,
            "accumulated_value": 0.0,
            "fringe_contribution": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "fringes": [],
            "created_by": user.pk,
            "updated_by": user.pk,
            "contact": None,
            "unit": None
        },
        {
            "id": subaccounts[1].pk,
            "identifier": "%s" % subaccounts[1].identifier,
            "description": subaccounts[1].description,
            "created_at": "2020-01-02 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[1].quantity,
            "rate": subaccounts[1].rate,
            "multiplier": subaccounts[1].multiplier,
            "type": "subaccount",
            "object_id": account.pk,
            "parent_type": "account",
            "nominal_value": 0.0,
            "accumulated_value": 0.0,
            "fringe_contribution": 0.0,
            "accumulated_fringe_contribution": 0.0,
            "markup_contribution": 0.0,
            "accumulated_markup_contribution": 0.0,
            "actual": 0.0,
            "children": [],
            "fringes": [],
            "created_by": user.pk,
            "updated_by": user.pk,
            "contact": None,
            "unit": None
        },
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_community_template_account_subaccounts(api_client, user,
        staff_user, create_template, create_template_account,
        create_template_subaccount):
    with signals.disable():
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
    with signals.disable():
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


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_subaccount(api_client, user, create_template_account,
        create_template, models):
    with signals.disable():
        template = create_template()
        account = create_template_account(parent=template)
    api_client.force_login(user)
    response = api_client.post(
        "/v1/accounts/%s/subaccounts/" % account.pk,
        data={
            'identifier': '100',
            'description': 'Test'
        }
    )
    assert response.status_code == 201
    subaccount = models.TemplateSubAccount.objects.first()
    assert subaccount.description == "Test"
    assert subaccount.identifier == "100"

    assert subaccount is not None
    assert response.json() == {
        "id": subaccount.pk,
        "identifier": '100',
        "description": 'Test',
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": None,
        "rate": None,
        "multiplier": None,
        "unit": None,
        "contact": None,
        "type": "subaccount",
        "object_id": account.pk,
        "parent_type": "account",
        "nominal_value": 0.0,
        "accumulated_value": 0.0,
        "fringe_contribution": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "markup_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "children": [],
        "fringes": [],
        "contact": None,
        "created_by": user.pk,
        "updated_by": user.pk,
    }
