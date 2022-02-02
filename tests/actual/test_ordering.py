def test_ordering_bulk_create(api_client, user, models, budget_df):
    budget = budget_df.create_budget()

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/budgets/%s/bulk-create-actuals/" % budget.pk,
        format='json',
        data={'data': [{}, {}, {}]}
    )
    assert response.status_code == 201
    actuals = models.Actual.objects.all()
    assert len(actuals) == 3
    assert [a.order for a in actuals] == ["n", "t", "w"]


def test_move_actual_down(api_client, user, models, budget_df, create_actual):
    budget = budget_df.create_budget()
    actuals = create_actual(budget=budget, count=10)
    assert [a.order for a in actuals] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in actuals] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/actuals/%s/" % actuals[4].pk, data={
        'previous': actuals[1].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'v'

    actuals = models.Actual.objects.all()
    assert [a.pk for a in actuals] == [1, 2, 5, 3, 4, 6, 7, 8, 9, 10]


def test_move_actual_to_start(api_client, user, models, budget_df,
        create_actual):
    budget = budget_df.create_budget()
    actuals = create_actual(count=10, budget=budget)
    assert [c.order for c in actuals] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [c.pk for c in actuals] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actuals[4].pk,
        format='json',
        data={'previous': None}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'h'

    actuals = models.Actual.objects.all()
    assert [a.pk for a in actuals] == [5, 1, 2, 3, 4, 6, 7, 8, 9, 10]


def test_move_actual_to_end(api_client, user, models, create_actual, budget_df):
    budget = budget_df.create_budget()
    actuals = create_actual(count=10, budget=budget)
    assert [a.order for a in actuals] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in actuals] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/actuals/%s/" % actuals[4].pk,
        format='json',
        data={'previous': actuals[9].pk}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwyntw'

    actuals = models.Actual.objects.all()
    assert [a.pk for a in actuals] == [1, 2, 3, 4, 6, 7, 8, 9, 10, 5]


def test_move_actual_self_referential(api_client, user, create_actual,
        budget_df):
    budget = budget_df.create_budget()
    actuals = create_actual(count=10, budget=budget)
    assert [a.order for a in actuals] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in actuals] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/actuals/%s/" % actuals[3].pk, data={
        'previous': actuals[3].pk
    })
    assert response.status_code == 400


def test_move_actual_same_order(api_client, user, models, budget_df,
        create_actual):
    budget = budget_df.create_budget()
    actuals = create_actual(budget=budget, count=10)
    assert [a.order for a in actuals] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in actuals] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/actuals/%s/" % actuals[3].pk, data={
        'previous': actuals[2].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'y'

    actuals = models.Actual.objects.all()
    assert [a.pk for a in actuals] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def test_move_actual_up(api_client, user, models, budget_df, create_actual):
    budget = budget_df.create_budget()
    actuals = create_actual(budget=budget, count=10)
    assert [a.order for a in actuals] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in actuals] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/actuals/%s/" % actuals[4].pk, data={
        'previous': actuals[8].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwynk'

    actuals = models.Actual.objects.all()
    assert [a.pk for a in actuals] == [1, 2, 3, 4, 6, 7, 8, 9, 5, 10]
