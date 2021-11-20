def test_ordering_bulk_create(api_client, user, models, budget_f):
    budget = budget_f.create_budget()

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/%ss/%s/bulk-create-fringes/" % (budget_f.context, budget.pk),
        format='json',
        data={'data': [{}, {}, {}]}
    )
    assert response.status_code == 201
    fringes = models.Fringe.objects.all()
    assert len(fringes) == 3
    assert [f.order for f in fringes] == ["n", "t", "w"]


def test_move_fringe_down(api_client, user, models, budget_f, create_fringes):
    budget = budget_f.create_budget()
    fringes = create_fringes(budget=budget, count=10)
    assert [a.order for a in fringes] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [f.pk for f in fringes] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/fringes/%s/" % fringes[4].pk, data={
        'order': 8
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwynk'

    fringes = models.Fringe.objects.all()
    assert [f.pk for f in fringes] == [1, 2, 3, 4, 6, 7, 8, 9, 5, 10]


def test_move_fringe_same_order(api_client, user, models, budget_f,
        create_fringes):
    budget = budget_f.create_budget()
    fringes = create_fringes(budget=budget, count=10)
    assert [a.order for a in fringes] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [f.pk for f in fringes] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/fringes/%s/" % fringes[3].pk, data={
        'order': 3
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'y'

    fringes = models.Fringe.objects.all()
    assert [f.pk for f in fringes] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def test_move_fringe_up(api_client, user, models, budget_f, create_fringes):
    budget = budget_f.create_budget()
    fringes = create_fringes(budget=budget, count=10)
    assert [a.order for a in fringes] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [f.pk for f in fringes] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/fringes/%s/" % fringes[4].pk, data={
        'order': 2
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'v'

    fringes = models.Fringe.objects.all()
    assert [f.pk for f in fringes] == [1, 2, 5, 3, 4, 6, 7, 8, 9, 10]
