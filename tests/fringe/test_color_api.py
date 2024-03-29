def test_get_fringe_colors(api_client, user, colors):
    api_client.force_login(user)
    response = api_client.get("/v1/fringes/colors/")
    assert response.json()['count'] == 2
    assert response.json()['data'] == [colors[0].code, colors[1].code]


def test_update_fringe_color(api_client, user, f, models, budget_f):
    color = f.create_color(code='#AFAFAF', content_types=[models.Fringe])
    another_color = f.create_color(code='#000000', content_types=[models.Fringe])
    budget = budget_f.create_budget()
    fringe = f.create_fringe(budget=budget, color=color)

    api_client.force_login(user)
    response = api_client.patch("/v1/fringes/%s/" % fringe.pk, {
        'color': another_color.code
    })
    assert response.status_code == 200
    assert response.json()['color'] == '#000000'
    fringe.refresh_from_db()
    assert fringe.color.code == '#000000'


def test_update_fringe_color_invalid_code(api_client, user, f, models, budget_f):
    color = f.create_color(code='#AFAFAF', content_types=[models.Fringe])
    budget = budget_f.create_budget()
    fringe = f.create_fringe(budget=budget, color=color)

    api_client.force_login(user)
    response = api_client.patch("/v1/fringes/%s/" % fringe.pk, {
        'color': '#AFff2AF2'
    })
    assert response.json() == {'errors': [{
        'message': (
            'This code "#AFff2AF2" is not a valid hexadecimal color code.'),
        'code': 'invalid_type',
        'error_type': 'field',
        'field': 'color'
    }]}
