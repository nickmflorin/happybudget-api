def test_unit_properly_serializes(api_client, user, create_actual_type):
    types = [
        create_actual_type(title='Vendor'),
        create_actual_type(title='Company')
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/actuals/types/")
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            'id': types[0].pk,
            'title': types[0].title,
            'plural_title': types[0].plural_title,
            'order': types[0].order,
            'color': types[0].color.code
        },
        {
            'id': types[1].pk,
            'title': types[1].title,
            'plural_title': types[1].plural_title,
            'order': types[1].order,
            'color': types[1].color.code
        }
    ]
