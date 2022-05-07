def test_ordering_bulk_create(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-children/" % account.pk,
        format='json',
        data={'data': [{}, {}, {}]}
    )
    assert response.status_code == 200
    subaccounts = models.SubAccount.objects.all()
    assert len(subaccounts) == 3
    assert [sub.order for sub in subaccounts] == ["n", "t", "w"]


def test_move_account_down(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(parent=budget, count=10)
    assert [a.order for a in accounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % accounts[4].pk, data={
        'previous': accounts[1].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'v'

    accounts = models.Account.objects.all()
    assert [a.pk for a in accounts] == [1, 2, 5, 3, 4, 6, 7, 8, 9, 10]


def test_move_account_to_start(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(parent=budget, count=10)
    assert [a.order for a in accounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/" % accounts[4].pk,
        format='json',
        data={'previous': None}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'h'

    accounts = models.Account.objects.all()
    assert [a.pk for a in accounts] == [5, 1, 2, 3, 4, 6, 7, 8, 9, 10]


def test_move_account_to_end(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(parent=budget, count=10)
    assert [a.order for a in accounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/" % accounts[4].pk,
        format='json',
        data={'previous': accounts[9].pk}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwyntw'

    accounts = models.Account.objects.all()
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 6, 7, 8, 9, 10, 5]


def test_move_account_self_referential(api_client, user, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(parent=budget, count=10)
    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % accounts[3].pk, data={
        'previous': accounts[3].pk
    })
    assert response.status_code == 400


def test_move_account_same_order(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(parent=budget, count=10)
    assert [a.order for a in accounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % accounts[3].pk, data={
        'previous': accounts[2].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'y'

    accounts = models.Account.objects.all()
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def test_move_account_up(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(parent=budget, count=10)
    assert [a.order for a in accounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % accounts[4].pk, data={
        'previous': accounts[8].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwynk'

    accounts = models.Account.objects.all()
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 6, 7, 8, 9, 5, 10]
