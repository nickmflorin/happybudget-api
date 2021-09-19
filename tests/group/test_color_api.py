def test_get_group_colors(api_client, user, colors):
    api_client.force_login(user)
    response = api_client.get("/v1/groups/colors/")
    assert response.json()['count'] == 2
    assert response.json()['data'] == [colors[0].code, colors[1].code]


def test_update_group_color(api_client, user, create_color, models,
        create_group, create_budget):
    color = create_color(code='#AFAFAF', content_types=[models.Group])
    another_color = create_color(code='#000000', content_types=[models.Group])
    budget = create_budget()
    group = create_group(parent=budget, color=color)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, {
        'color': another_color.code
    })
    assert response.status_code == 200
    assert response.json()['color'] == '#000000'
    group.refresh_from_db()
    assert group.color.code == '#000000'


def test_update_group_color_invalid_code(api_client, user, create_color, models,
        create_group, create_budget):
    color = create_color(code='#AFAFAF', content_types=[models.Group])
    budget = create_budget()
    group = create_group(parent=budget, color=color)

    api_client.force_login(user)
    response = api_client.patch("/v1/groups/%s/" % group.pk, {
        'color': '#AFff2AF2'
    })
    assert response.json() == {'errors': [{
        'message': 'This code "#AFff2AF2" is not a valid hexadecimal color code.',  # noqa
        'code': 'invalid_type',
        'error_type': 'field',
        'field': 'color'
    }]}
