from copy import deepcopy
import pytest

from greenbudget.app.history.models import FieldAlterationEvent, CreateEvent


@pytest.mark.freeze_time('2020-01-01')
def test_get_accounts_history(api_client, create_budget, user):
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

    assert CreateEvent.objects.count() == 1
    assert FieldAlterationEvent.objects.count() == 2
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
def test_get_account_history(api_client, create_budget, create_account, user):
    budget = create_budget()
    account = create_account(
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

    assert FieldAlterationEvent.objects.count() == 2
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
