def test_ordering_bulk_create(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-create-subaccounts/" % subaccount.pk,
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
    subaccounts = budget_f.create_subaccounts(parent=subaccount, count=10)
    assert [a.order for a in subaccounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/" % subaccounts[4].pk,
        data={'order': 8}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwynk'

    subaccounts = models.SubAccount.objects.filter_by_parent(subaccount).all()
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 7, 8, 9, 10, 6, 11]


def test_move_subaccount_same_order(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = budget_f.create_subaccounts(parent=subaccount, count=10)
    assert [a.order for a in subaccounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/" % subaccounts[3].pk,
        data={'order': 3}
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
    subaccounts = budget_f.create_subaccounts(parent=subaccount, count=10)

    assert [a.order for a in subaccounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/" % subaccounts[4].pk,
        data={'order': 2}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'v'

    subaccounts = models.SubAccount.objects.filter_by_parent(subaccount).all()
    assert [a.pk for a in subaccounts] == [2, 3, 6, 4, 5, 7, 8, 9, 10, 11]


def test_move_subaccount_new_group(api_client, user, models, budget_f,
        create_groups):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    groups = create_groups(parent=subaccount, count=2)
    subaccounts = budget_f.create_subaccounts(parent=subaccount, count=10)

    subaccounts[4].group = groups[0]
    subaccounts[4].save()

    assert [a.order for a in subaccounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/subaccounts/%s/" % subaccounts[4].pk,
        data={'order': 8, 'group': groups[1].pk}
    )
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwynk'

    subaccounts[4].refresh_from_db()
    assert subaccounts[4].group == groups[1]

    subaccounts = models.SubAccount.objects.filter_by_parent(subaccount).all()
    assert [a.pk for a in subaccounts] == [2, 3, 4, 5, 7, 8, 9, 10, 6, 11]
