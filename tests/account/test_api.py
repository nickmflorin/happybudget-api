from copy import deepcopy
import pytest

from greenbudget.app.account.models import Account
from greenbudget.app.history.models import FieldAlterationEvent


@pytest.mark.freeze_time('2020-01-01')
def test_get_accounts(api_client, user, create_account, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    accounts = [create_account(budget=budget), create_account(budget=budget)]
    response = api_client.get("/v1/budgets/%s/accounts/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            "id": accounts[0].pk,
            "identifier": "%s" % accounts[0].identifier,
            "description": accounts[0].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "access": [],
            "budget": budget.pk,
            "type": "account",
            "estimated": None,
            "variance": None,
            "actual": None,
            "subaccounts": [],
            "ancestors": [{
                "type": "budget",
                "id": budget.pk,
                "identifier": budget.name
            }],
            "created_by": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name,
                "profile_image": None,
            },
            "updated_by": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name,
                "profile_image": None,
            }
        },
        {
            "id": accounts[1].pk,
            "identifier": "%s" % accounts[1].identifier,
            "description": accounts[1].description,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            "access": [],
            "budget": budget.pk,
            "type": "account",
            "estimated": None,
            "variance": None,
            "actual": None,
            "subaccounts": [],
            "ancestors": [{
                "type": "budget",
                "id": budget.pk,
                "identifier": budget.name
            }],
            "created_by": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name,
                "profile_image": None,
            },
            "updated_by": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "is_superuser": user.is_superuser,
                "is_staff": user.is_staff,
                "full_name": user.full_name,
                "profile_image": None,
            }
        }
    ]


@pytest.mark.freeze_time('2020-01-01')
def test_get_account(api_client, user, create_account, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(budget=budget)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": account.pk,
        "identifier": "%s" % account.identifier,
        "description": account.description,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "budget": account.budget.pk,
        "type": "account",
        "estimated": None,
        "variance": None,
        "actual": None,
        "subaccounts": [],
        "ancestors": [{
            "type": "budget",
            "id": account.budget.pk,
            "identifier": account.budget.name
        }],
        "created_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name,
            "profile_image": None,
        },
        "updated_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name,
            "profile_image": None,
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_account(api_client, user, create_budget):
    api_client.force_login(user)
    budget = create_budget()
    response = api_client.post("/v1/budgets/%s/accounts/" % budget.pk, data={
        'identifier': 'new_account'
    })
    assert response.status_code == 201

    account = Account.objects.first()
    assert account is not None

    assert response.json() == {
        "id": account.pk,
        "identifier": 'new_account',
        "description": None,
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "budget": budget.pk,
        "type": "account",
        "estimated": None,
        "variance": None,
        "actual": None,
        "subaccounts": [],
        "ancestors": [{
            "type": "budget",
            "id": budget.pk,
            "identifier": budget.name
        }],
        "created_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name,
            "profile_image": None,
        },
        "updated_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name,
            "profile_image": None,
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_account_duplicate_number(api_client, user, create_budget,
        create_account):
    api_client.force_login(user)
    budget = create_budget()
    create_account(budget=budget, identifier="new_account")
    response = api_client.post("/v1/budgets/%s/accounts/" % budget.pk, data={
        'identifier': 'new_account'
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_update_account(api_client, user, create_budget, create_account):
    api_client.force_login(user)
    budget = create_budget()
    account = create_account(
        budget=budget,
        identifier="original_identifier"
    )
    response = api_client.patch("/v1/accounts/%s/" % account.pk, data={
        'identifier': 'new_account',
        'description': 'Account description',
    })
    assert response.status_code == 200
    assert response.json() == {
        "id": account.pk,
        "identifier": 'new_account',
        "description": 'Account description',
        "created_at": "2020-01-01 00:00:00",
        "updated_at": "2020-01-01 00:00:00",
        "access": [],
        "budget": budget.pk,
        "type": "account",
        "estimated": None,
        "variance": None,
        "actual": None,
        "subaccounts": [],
        "ancestors": [{
            "type": "budget",
            "id": budget.pk,
            "identifier": budget.name
        }],
        "created_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name,
            "profile_image": None,
        },
        "updated_by": {
            "id": user.pk,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "full_name": user.full_name,
            "profile_image": None,
        }
    }
    account.refresh_from_db()
    assert account.identifier == "new_account"
    assert account.description == "Account description"


@pytest.mark.freeze_time('2020-01-01')
def test_update_account_duplicate_number(api_client, user, create_budget,
        create_account):
    api_client.force_login(user)
    budget = create_budget()
    create_account(identifier="identifier", budget=budget)
    account = create_account(
        budget=budget,
        identifier="original_identifier"
    )
    response = api_client.patch("/v1/accounts/%s/" % account.pk, data={
        'identifier': 'identifier',
        'description': 'Account description',
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_get_accounts_history(api_client, create_budget, create_account, user):
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
    response = api_client.get("/v1/budgets/%s/accounts/history/" % budget.pk)
    assert response.status_code == 200

    assert FieldAlterationEvent.objects.count() == 2
    assert response.json()['count'] == 2
    serialized_events = [
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "Account description",
            "old_value": account.description,
            "field": "description",
            "object_id": account.pk,
            "content_object_type": "account",
            "type": "field_alteration",
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
            "object_id": account.pk,
            "content_object_type": "account",
            "type": "field_alteration",
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
            "object_id": account.pk,
            "content_object_type": "account",
            "type": "field_alteration",
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
            "object_id": account.pk,
            "content_object_type": "account",
            "type": "field_alteration",
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
