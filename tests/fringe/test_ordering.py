def test_ordering_bulk_create(api_client, user, models, budget_f):
    budget = budget_f.create_budget()

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-create-fringes/" % budget.pk,
        format='json',
        data={'data': [{}, {}, {}]}
    )
    assert response.status_code == 200
    fringes = models.Fringe.objects.all()
    assert len(fringes) == 3
    assert [f.order for f in fringes] == ["n", "t", "w"]


def test_move_fringe_down(api_client, user, models, budget_f, f):
    budget = budget_f.create_budget()
    fringes = f.create_fringe(budget=budget, count=10)
    assert [a.order for a in fringes] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [f.pk for f in fringes] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/fringes/%s/" % fringes[4].pk, data={
        'previous': fringes[1].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'v'

    fringes = models.Fringe.objects.all()
    assert [f.pk for f in fringes] == [1, 2, 5, 3, 4, 6, 7, 8, 9, 10]


def test_move_fringe_to_start(api_client, user, models, budget_f, f):
    budget = budget_f.create_budget()
    fringes = f.create_fringe(count=10, budget=budget)
    assert [c.order for c in fringes] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [c.pk for c in fringes] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/fringes/%s/" % fringes[4].pk,
        format='json',
        data={'previous': None}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'h'

    fringes = models.Fringe.objects.all()
    assert [a.pk for a in fringes] == [5, 1, 2, 3, 4, 6, 7, 8, 9, 10]


def test_move_fringe_to_end(api_client, user, models, f, budget_f):
    budget = budget_f.create_budget()
    fringes = f.create_fringe(count=10, budget=budget)
    assert [a.order for a in fringes] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in fringes] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/fringes/%s/" % fringes[4].pk,
        format='json',
        data={'previous': fringes[9].pk}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwyntw'

    fringes = models.Fringe.objects.all()
    assert [a.pk for a in fringes] == [1, 2, 3, 4, 6, 7, 8, 9, 10, 5]


def test_move_fringe_self_referential(api_client, user, budget_f, f):
    budget = budget_f.create_budget()
    fringes = f.create_fringe(count=10, budget=budget)
    assert [a.order for a in fringes] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in fringes] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/fringes/%s/" % fringes[3].pk, data={
        'previous': fringes[3].pk
    })
    assert response.status_code == 400


def test_move_fringe_same_order(api_client, user, models, budget_f, f):
    budget = budget_f.create_budget()
    fringes = f.create_fringe(budget=budget, count=10)
    assert [a.order for a in fringes] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [f.pk for f in fringes] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/fringes/%s/" % fringes[3].pk, data={
        'previous': fringes[2].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'y'

    fringes = models.Fringe.objects.all()
    assert [f.pk for f in fringes] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def test_move_fringe_up(api_client, user, models, budget_f, f):
    budget = budget_f.create_budget()
    fringes = f.create_fringe(budget=budget, count=10)
    assert [a.order for a in fringes] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [f.pk for f in fringes] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/fringes/%s/" % fringes[4].pk, data={
        'previous': fringes[8].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwynk'

    fringes = models.Fringe.objects.all()
    assert [f.pk for f in fringes] == [1, 2, 3, 4, 6, 7, 8, 9, 5, 10]
