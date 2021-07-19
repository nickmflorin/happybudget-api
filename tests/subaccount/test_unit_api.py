import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_unit_properly_serializes(api_client, user, create_subaccount_unit):
    units = [
        create_subaccount_unit(),
        create_subaccount_unit()
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/units/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            'id': units[0].pk,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            'title': units[0].title,
            'plural_title': units[0].plural_title,
            'order': units[0].order,
            'color': units[0].color.code
        },
        {
            'id': units[1].pk,
            "created_at": "2020-01-01 00:00:00",
            "updated_at": "2020-01-01 00:00:00",
            'title': units[1].title,
            'plural_title': units[1].plural_title,
            'order': units[1].order,
            'color': units[1].color.code
        }
    ]
