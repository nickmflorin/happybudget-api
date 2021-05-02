def test_get_group_colors(api_client, user, create_color, models):
    colors = [
        create_color(content_types=[models.Group]),
        create_color(content_types=[models.Group])
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/groups/colors/")
    assert response.json()['count'] == 2
    assert response.json()['data'] == [colors[0].code, colors[1].code]
