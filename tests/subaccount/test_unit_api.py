from django.test import override_settings
import mock

from greenbudget.app.subaccount.views import SubAccountUnitViewSet


def test_unit_properly_serializes(api_client, user, units):
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/units/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            'id': units[0].pk,
            'title': units[0].title,
            'plural_title': units[0].plural_title,
            'order': units[0].order,
            'color': units[0].color.code
        },
        {
            'id': units[1].pk,
            'title': units[1].title,
            'plural_title': units[1].plural_title,
            'order': units[1].order,
            'color': units[1].color.code
        }
    ]


@override_settings(CACHE_ENABLED=True)
def test_units_cached(api_client, user, units):
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/units/")
    assert response.status_code == 200
    assert response.json()['count'] == 2

    with mock.patch.object(SubAccountUnitViewSet, 'get_queryset') as m:
        api_client.force_login(user)
        response = api_client.get("/v1/subaccounts/units/")

    assert not m.called


@override_settings(CACHE_ENABLED=True)
def test_cache_invalidated_on_save(api_client, user, f, units):
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/units/")
    assert response.status_code == 200
    assert response.json()['count'] == 2

    f.create_subaccount_unit()

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/units/")
    assert response.status_code == 200
    assert response.json()['count'] == 3


@override_settings(CACHE_ENABLED=True)
def test_cache_invalidated_on_delete(api_client, user, units):
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/units/")
    assert response.status_code == 200
    assert response.json()['count'] == 2

    units[0].delete()

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/units/")
    assert response.status_code == 200
    assert response.json()['count'] == 1
