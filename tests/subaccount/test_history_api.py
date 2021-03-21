from copy import deepcopy
import pytest

from greenbudget.app.history.models import FieldAlterationEvent


@pytest.mark.freeze_time('2020-01-01')
def test_get_account_subaccounts_history(api_client, create_budget, user,
        create_sub_account, create_account):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(
        parent=account,
        name="Original Name",
        description="Original Description",
        identifier="old_identifier",
        budget=budget
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "name": "New Name",
        "description": "New Description",
        "identifier": "new_identifier",
        "quantity": 10,
        "rate": 1.5
    })
    response = api_client.get(
        "/v1/budgets/%s/accounts/%s/subaccounts/history/"
        % (budget.pk, account.pk)
    )
    assert response.status_code == 200

    assert FieldAlterationEvent.objects.count() == 5

    assert response.json()['count'] == 5
    serialized_events = [
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New Description",
            "old_value": "Original Description",
            "field": "description",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "new_identifier",
            "old_value": "old_identifier",
            "field": "identifier",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": 1.5,
            "old_value": subaccount.rate,
            "field": "rate",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New Name",
            "old_value": "Original Name",
            "field": "name",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": 10,
            "old_value": None,
            "field": "quantity",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        }
    ]
    for serialized_event in response.json()['data']:
        event_without_id = deepcopy(serialized_event)
        del event_without_id['id']
        assert event_without_id in serialized_events


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount_subaccounts_history(api_client, create_budget, user,
        create_sub_account, create_account):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    parent_subaccount = create_sub_account(parent=account, budget=budget)
    subaccount = create_sub_account(
        parent=parent_subaccount,
        name="Original Name",
        description="Original Description",
        identifier="old_identifier",
        budget=budget
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "name": "New Name",
        "description": "New Description",
        "identifier": "new_identifier",
        "quantity": 10,
        "rate": 1.5
    })
    response = api_client.get(
        "/v1/subaccounts/%s/subaccounts/history/"
        % parent_subaccount.pk
    )
    assert response.status_code == 200
    assert FieldAlterationEvent.objects.count() == 5

    assert response.json()['count'] == 5
    serialized_events = [
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New Description",
            "old_value": "Original Description",
            "field": "description",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "new_identifier",
            "old_value": "old_identifier",
            "field": "identifier",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": 1.5,
            "old_value": subaccount.rate,
            "field": "rate",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New Name",
            "old_value": "Original Name",
            "field": "name",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": 10,
            "old_value": None,
            "field": "quantity",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        }
    ]
    for serialized_event in response.json()['data']:
        event_without_id = deepcopy(serialized_event)
        del event_without_id['id']
        assert event_without_id in serialized_events


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount_history(api_client, create_budget, create_account,
        create_sub_account, user):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(
        parent=account,
        name="Original Name",
        description="Original Description",
        identifier="old_identifier",
        budget=budget
    )
    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "name": "New Name",
        "description": "New Description",
        "identifier": "new_identifier",
        "quantity": 10,
        "rate": 1.5
    })
    response = api_client.get("/v1/subaccounts/%s/history/" % subaccount.pk)
    assert response.status_code == 200

    assert FieldAlterationEvent.objects.count() == 5

    assert response.json()['count'] == 5
    serialized_events = [
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New Description",
            "old_value": "Original Description",
            "field": "description",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "new_identifier",
            "old_value": "old_identifier",
            "field": "identifier",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": 1.5,
            "old_value": subaccount.rate,
            "field": "rate",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "New Name",
            "old_value": "Original Name",
            "field": "name",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        },
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": 10,
            "old_value": None,
            "field": "quantity",
            "type": "field_alteration",
            "content_object": {
                'id': subaccount.pk,
                'identifier': 'new_identifier',
                'type': 'subaccount',
                'description': 'New Description'
            },
            "user": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image": None,
            }
        }
    ]
    for serialized_event in response.json()['data']:
        event_without_id = deepcopy(serialized_event)
        del event_without_id['id']
        assert event_without_id in serialized_events