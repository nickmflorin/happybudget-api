def test_ordering_bulk_create(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-subaccounts/" % account.pk,
        format='json',
        data={'data': [{}, {}, {}]}
    )
    assert response.status_code == 201
    subaccounts = models.SubAccount.objects.all()
    assert len(subaccounts) == 3
    assert [sub.order for sub in subaccounts] == ["n", "t", "w"]


def test_move_account_down(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_accounts(parent=budget, count=10)
    assert [a.order for a in accounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % accounts[4].pk, data={
        'order': 8
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwynk'

    accounts = models.Account.objects.all()
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 6, 7, 8, 9, 5, 10]


def test_move_account_down_one(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_accounts(parent=budget, count=10)
    assert [a.order for a in accounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % accounts[0].pk, data={
        'order': 1
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'v'

    accounts = models.Account.objects.all()
    assert [a.pk for a in accounts] == [2, 1, 3, 4, 5, 6, 7, 8, 9, 10]


def test_move_account_same_order(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_accounts(parent=budget, count=10)
    assert [a.order for a in accounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % accounts[3].pk, data={
        'order': 3
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'y'

    accounts = models.Account.objects.all()
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def test_move_account_up(api_client, user, models, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_accounts(parent=budget, count=10)
    assert [a.order for a in accounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % accounts[4].pk, data={
        'order': 2
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'v'

    accounts = models.Account.objects.all()
    assert [a.pk for a in accounts] == [1, 2, 5, 3, 4, 6, 7, 8, 9, 10]


def test_move_account_new_group(api_client, user, models, budget_f,
        create_group):
    budget = budget_f.create_budget()
    groups = [
        create_group(parent=budget),
        create_group(parent=budget)
    ]
    accounts = budget_f.create_accounts(parent=budget, count=10)
    accounts[4].group = groups[0]
    accounts[4].save()
    assert [a.order for a in accounts] == \
        ['n', 't', 'w', 'y', 'yn', 'ynt', 'yntw', 'yntwy', 'yntwyn', 'yntwynt']
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    api_client.force_login(user)
    response = api_client.patch("/v1/accounts/%s/" % accounts[4].pk, data={
        'order': 8,
        'group': groups[1].pk
    })
    assert response.status_code == 200
    assert 'order' in response.json()
    assert response.json()['order'] == 'yntwynk'

    accounts[4].refresh_from_db()
    assert accounts[4].group == groups[1]

    accounts = models.Account.objects.all()
    assert [a.pk for a in accounts] == [1, 2, 3, 4, 6, 7, 8, 9, 5, 10]
