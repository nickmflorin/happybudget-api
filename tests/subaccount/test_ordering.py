def test_ordering_bulk_create(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-create-children/" % subaccount.pk,
        format='json',
        data={'data': [{}, {}, {}]}
    )
    assert response.status_code == 201
    subaccounts = models.SubAccount.objects.filter_by_parent(subaccount).all()
    assert len(subaccounts) == 3
    assert [sub.order for sub in subaccounts] == ["n", "t", "w"]


def test_move_subaccount_down(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = budget_f.create_subaccount(parent=subaccount, count=10)
    assert [a.order for a in subaccounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/" % subaccounts[4].pk,
        data={'previous': subaccounts[1].pk}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'v'

    subaccounts = models.SubAccount.objects.filter_by_parent(subaccount).all()
    assert [a.pk for a in subaccounts] == [2, 3, 6, 4, 5, 7, 8, 9, 10, 11]


def test_move_subaccount_to_start(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = budget_f.create_subaccount(parent=subaccount, count=10)
    assert [a.order for a in subaccounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/" % subaccounts[4].pk,
        format='json',
        data={'previous': None}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'h'

    subaccounts = models.SubAccount.objects.filter_by_parent(subaccount).all()
    assert [a.pk for a in subaccounts] == [6, 2, 3, 4, 5, 7, 8, 9, 10, 11]


def test_move_subaccount_to_end(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = budget_f.create_subaccount(parent=subaccount, count=10)
    assert [a.order for a in subaccounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/" % subaccounts[4].pk,
        format='json',
        data={'previous': subaccounts[9].pk}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwyntw'

    subaccounts = models.SubAccount.objects.filter_by_parent(subaccount).all()
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 7, 8, 9, 10, 11, 6]


def test_move_subaccount_self_referential(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = budget_f.create_subaccount(parent=subaccount, count=10)
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/" % subaccounts[3].pk,
        data={'previous': subaccounts[3].pk}
    )
    assert response.status_code == 400


def test_move_subaccount_same_order(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = budget_f.create_subaccount(parent=subaccount, count=10)
    assert [a.order for a in subaccounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/" % subaccounts[3].pk,
        data={'previous': subaccounts[2].pk}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'y'

    subaccounts = models.SubAccount.objects.filter_by_parent(subaccount).all()
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


def test_move_subaccount_up(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = budget_f.create_subaccount(parent=subaccount, count=10)

    assert [a.order for a in subaccounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/" % subaccounts[4].pk,
        data={'previous': subaccounts[8].pk}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwynk'

    subaccounts = models.SubAccount.objects.filter_by_parent(subaccount).all()
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 7, 8, 9, 10, 6, 11]
