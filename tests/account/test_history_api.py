from copy import deepcopy
import pytest

from django.test import override_settings

from greenbudget.app import signals


@pytest.mark.freeze_time('2020-01-01')
@override_settings(TRACK_MODEL_HISTORY=True)
def test_get_accounts_history(api_client, create_budget, user, models):
    budget = create_budget()
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/accounts/" % budget.pk, data={
        'identifier': 'original_identifier'
    })
    account_pk = response.json()['id']
    assert response.status_code == 201
    response = api_client.patch("/v1/accounts/%s/" % account_pk, data={
        'identifier': 'new_identifier',
        'description': 'Account description',
    })
    assert response.status_code == 200
    response = api_client.get("/v1/budgets/%s/accounts/history/" % budget.pk)
    assert response.status_code == 200

    assert models.CreateEvent.objects.count() == 1
    assert models.FieldAlterationEvent.objects.count() == 2
    assert response.json()['count'] == 3
    serialized_events = [
        {
            "created_at": "2020-01-01 00:00:00",
            "type": "create",
            "content_object": {
                'id': account_pk,
                'identifier': 'new_identifier',
                'type': 'account',
                'description': 'Account description'
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
            "new_value": "Account description",
            "old_value": None,
            "field": "description",
            "type": "field_alteration",
            "content_object": {
                'id': account_pk,
                'identifier': 'new_identifier',
                'type': 'account',
                'description': 'Account description'
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
            "old_value": "original_identifier",
            "field": "identifier",
            "type": "field_alteration",
            "content_object": {
                'id': account_pk,
                'identifier': 'new_identifier',
                'type': 'account',
                'description': 'Account description'
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
@override_settings(TRACK_MODEL_HISTORY=True)
def test_get_account_history(api_client, create_budget, create_budget_account,
        user, models):
    with signals.post_create_by_user.disable():
        budget = create_budget()
        account = create_budget_account(
            budget=budget,
            identifier="original_identifier"
        )
    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % account.pk, data={
        'identifier': 'new_identifier',
        'description': 'Account description',
    })
    response = api_client.get("/v1/accounts/%s/history/" % account.pk)
    assert response.status_code == 200

    assert models.FieldAlterationEvent.objects.count() == 2
    assert response.json()['count'] == 2
    serialized_events = [
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "Account description",
            "old_value": account.description,
            "field": "description",
            "type": "field_alteration",
            "content_object": {
                'id': account.pk,
                'identifier': 'new_identifier',
                'type': 'account',
                'description': 'Account description'
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
            "old_value": "original_identifier",
            "field": "identifier",
            "type": "field_alteration",
            "content_object": {
                'id': account.pk,
                'identifier': 'new_identifier',
                'type': 'account',
                'description': 'Account description'
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
@override_settings(TRACK_MODEL_HISTORY=True)
def test_get_account_subaccounts_history(api_client, create_budget, user,
        create_budget_subaccount, create_budget_account, models):

    with signals.post_create_by_user.disable():
        api_client.force_login(user)
        budget = create_budget()
        account = create_budget_account(budget=budget)
        subaccount = create_budget_subaccount(
            parent=account,
            description="Original Description",
            identifier="old_identifier"
        )

    api_client.force_login(user)
    response = api_client.patch("/v1/subaccounts/%s/" % subaccount.pk, data={
        "description": "New Description",
        "identifier": "new_identifier",
        "quantity": 10,
        "rate": 1.5
    })
    response = api_client.get(
        "/v1/accounts/%s/subaccounts/history/" % account.pk)
    assert response.status_code == 200

    assert models.FieldAlterationEvent.objects.count() == 4

    assert response.json()['count'] == 4
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
                'description': 'New Description',
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
                'description': 'New Description',
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
                'description': 'New Description',
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
                'description': 'New Description',
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
