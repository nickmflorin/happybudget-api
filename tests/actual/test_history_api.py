from copy import deepcopy
import pytest

from greenbudget.app.history.models import FieldAlterationEvent


@pytest.mark.freeze_time('2020-01-01')
def test_get_actuals_history(api_client, create_budget, create_account,
        create_actual, user):
    budget = create_budget()
    account = create_account(budget=budget)
    actual = create_actual(parent=account, budget=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actual.pk,
        data={
            "vendor": "Vendor Name",
            "payment_id": "Payment ID",
        }
    )
    response = api_client.get("/v1/budgets/%s/actuals/history/" % budget.pk)
    assert response.status_code == 200

    assert FieldAlterationEvent.objects.count() == 2
    assert response.json()['count'] == 2

    serialized_events = [
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "Vendor Name",
            "old_value": actual.vendor,
            "field": "vendor",
            "type": "field_alteration",
            "content_object": {
                'id': actual.pk,
                'type': 'actual',
                'description': actual.description,
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
            "new_value": "Payment ID",
            "old_value": actual.payment_id,
            "field": "payment_id",
            "type": "field_alteration",
            "content_object": {
                'id': actual.pk,
                'type': 'actual',
                'description': actual.description,
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
def test_get_actual_history(api_client, create_budget, create_account, user,
        create_actual):
    budget = create_budget()
    account = create_account(budget=budget)
    actual = create_actual(parent=account, budget=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actual.pk,
        data={
            "vendor": "Vendor Name",
            "payment_id": "Payment ID",
        }
    )
    response = api_client.get("/v1/actuals/%s/history/" % actual.pk)
    assert response.status_code == 200

    assert FieldAlterationEvent.objects.count() == 2
    assert response.json()['count'] == 2

    serialized_events = [
        {
            "created_at": "2020-01-01 00:00:00",
            "new_value": "Vendor Name",
            "old_value": actual.vendor,
            "field": "vendor",
            "type": "field_alteration",
            "content_object": {
                'id': actual.pk,
                'type': 'actual',
                'description': actual.description,
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
            "new_value": "Payment ID",
            "old_value": actual.payment_id,
            "field": "payment_id",
            "type": "field_alteration",
            "content_object": {
                'id': actual.pk,
                'type': 'actual',
                'description': actual.description,
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
