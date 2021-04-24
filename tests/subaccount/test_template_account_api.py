import datetime
import pytest

from greenbudget.app.subaccount.models import TemplateSubAccount


@pytest.mark.freeze_time('2020-01-01')
def test_get_template_account_subaccounts(api_client, user, create_template,
        create_template_account, create_template_subaccount):
    template = create_template()
    account = create_template_account(budget=template)
    another_account = create_template_account(budget=template)
    subaccounts = [
        create_template_subaccount(
            parent=account,
            budget=template,
            created_at=datetime.datetime(2020, 1, 1)
        ),
        create_template_subaccount(
            parent=account,
            budget=template,
            created_at=datetime.datetime(2020, 1, 2)
        ),
        create_template_subaccount(parent=another_account, budget=template)
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": subaccounts[0].pk,
            "name": subaccounts[0].name,
            "identifier": "%s" % subaccounts[0].identifier,
            "description": subaccounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[0].quantity,
            "rate": subaccounts[0].rate,
            "multiplier": float(subaccounts[0].multiplier),
            "type": "subaccount",
            "object_id": account.pk,
            "budget": template.pk,
            "parent_type": "account",
            "account": account.pk,
            "estimated": None,
            "subaccounts": [],
            "fringes": [],
            "created_by": user.pk,
            "updated_by": user.pk,
            "group": None,
            "unit": {
                "id": subaccounts[0].unit,
                "name": TemplateSubAccount.UNITS[subaccounts[0].unit]
            },
            "ancestors": [
                {
                    "type": "template",
                    "id": template.pk,
                    "name": template.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "identifier": account.identifier,
                    "description": account.description,
                }
            ],
            "siblings": [{
                "id": subaccounts[1].id,
                "type": "subaccount",
                "identifier": subaccounts[1].identifier,
                "name": subaccounts[1].name,
                "description": subaccounts[1].description
            }],
        },
        {
            "id": subaccounts[1].pk,
            "name": subaccounts[1].name,
            "identifier": "%s" % subaccounts[1].identifier,
            "description": subaccounts[1].description,
            "created_at": "2020-01-02 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "quantity": subaccounts[1].quantity,
            "rate": subaccounts[1].rate,
            "multiplier": float(subaccounts[1].multiplier),
            "type": "subaccount",
            "object_id": account.pk,
            "budget": template.pk,
            "parent_type": "account",
            "account": account.pk,
            "estimated": None,
            "subaccounts": [],
            "fringes": [],
            "group": None,
            "created_by": user.pk,
            "updated_by": user.pk,
            "unit": {
                "id": subaccounts[1].unit,
                "name": TemplateSubAccount.UNITS[subaccounts[1].unit]
            },
            "ancestors": [
                {
                    "type": "template",
                    "id": template.pk,
                    "name": template.name,
                },
                {
                    "id": account.id,
                    "type": "account",
                    "identifier": account.identifier,
                    "description": account.description,
                }
            ],
            "siblings": [{
                "id": subaccounts[0].id,
                "type": "subaccount",
                "identifier": subaccounts[0].identifier,
                "name": subaccounts[0].name,
                "description": subaccounts[0].description
            }],
        },
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_create_template_subaccount(api_client, user, create_template_account,
        create_template):
    template = create_template()
    account = create_template_account(budget=template)
    api_client.force_login(user)
    response = api_client.post(
        "/v1/accounts/%s/subaccounts/" % account.pk,
        data={
            'name': 'New Subaccount',
            'identifier': '100',
            'description': 'Test'
        }
    )
    assert response.status_code == 201
    subaccount = TemplateSubAccount.objects.first()
    assert subaccount.name == "New Subaccount"
    assert subaccount.description == "Test"
    assert subaccount.identifier == "100"

    assert subaccount is not None
    assert response.json() == {
        "id": subaccount.pk,
        "name": 'New Subaccount',
        "identifier": '100',
        "description": 'Test',
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "quantity": None,
        "rate": None,
        "multiplier": None,
        "unit": None,
        "type": "subaccount",
        "object_id": account.pk,
        "budget": template.pk,
        "parent_type": "account",
        "account": account.pk,
        "estimated": None,
        "subaccounts": [],
        "fringes": [],
        "siblings": [],
        "group": None,
        "created_by": user.pk,
        "updated_by": user.pk,
        "ancestors": [
            {
                "type": "template",
                "id": template.pk,
                "name": template.name,
            },
            {
                "id": account.id,
                "type": "account",
                "identifier": account.identifier,
                "description": account.description,
            }
        ]
    }
