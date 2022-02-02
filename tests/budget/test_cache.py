from django.test import override_settings
from tests import need_to_write


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_delete(api_client, user, budget_f):
    budget = budget_f.create_budget()

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['id'] == budget.pk

    response = api_client.delete("/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert response.status_code == 204
    response = api_client.get("/v1/%ss/%s/" % (budget_f.context, budget.pk))

    # Note: This is kind of a dumb test, because this will return a 404
    # regardless of whether or not the instance was removed from the cache
    # because the Http404 is raised before the .retrieve() method executes.
    assert response.status_code == 404


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_save(api_client, user, budget_f):
    budget = budget_f.create_budget()

    api_client.force_login(user)
    response = api_client.get("/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['id'] == budget.pk

    response = api_client.patch(
        "/v1/%ss/%s/" % (budget_f.context, budget.pk),
        data={"name": "New Name"}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['name'] == 'New Name'


@override_settings(CACHE_ENABLED=True)
def test_caches_on_search(api_client, user, budget_f):
    budget = budget_f.create_budget()

    # These accounts should not be cached in the response because we will
    # be including a search query parameter.
    budget_f.create_account(parent=budget, identifier='Jack')
    budget_f.create_account(parent=budget, identifier='Jill')

    api_client.force_login(user)
    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200

    response = api_client.get(
        "/v1/%ss/%s/children/?search=jill" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_delete(api_client, user, budget_f):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]

    api_client.force_login(user)

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.delete("/v1/accounts/%s/" % accounts[0].pk)
    assert response.status_code == 204

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_update(api_client, user, budget_f):
    budget = budget_f.create_budget()
    accounts = [
        budget_f.create_account(parent=budget),
        budget_f.create_account(parent=budget)
    ]
    api_client.force_login(user)

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['identifier'] == accounts[0].identifier

    response = api_client.patch("/v1/accounts/%s/" % accounts[0].pk, data={
        'identifier': '1000'
    })
    assert response.status_code == 200

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['identifier'] == '1000'


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_create(api_client, user, budget_f):
    budget = budget_f.create_budget()
    budget_f.create_account(parent=budget, count=2)

    api_client.force_login(user)

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.post(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk),
        data={'identifier': '1000'}
    )
    assert response.status_code == 201

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 3


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_bulk_create(api_client, user, budget_f):
    budget = budget_f.create_budget()
    budget_f.create_account(parent=budget, count=2)

    api_client.force_login(user)

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/%ss/%s/bulk-create-children/" % (budget_f.context, budget.pk),
        format='json',
        data={'data': [{'identifier': '1000'}]}
    )
    assert response.status_code == 201
    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 3


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_add_fringe(api_client, user, budget_f,
        create_fringe):
    budget = budget_f.create_budget()
    fringes = [
        create_fringe(budget=budget, rate=0.5),
        create_fringe(budget=budget, rate=0.2)
    ]
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(
            parent=account,
            fringes=fringes,
            quantity=1,
            multiplier=1,
            rate=100,
        ),
        budget_f.create_subaccount(
            parent=account,
            fringes=fringes,
            quantity=2,
            multiplier=1,
            rate=100,
        )
    ]

    api_client.force_login(user)

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['accumulated_fringe_contribution'] == 210.0

    detail_response = api_client.get(
        "/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 210.0

    new_fringe = create_fringe(budget=budget, rate=0.5)
    subaccounts[0].fringes.add(new_fringe)

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['accumulated_fringe_contribution'] == 260.0

    detail_response = api_client.get(
        "/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 260.0


def test_caches_invalidated_on_update_fringe(api_client, user, budget_f,
        create_fringe):
    budget = budget_f.create_budget()
    fringes = [
        create_fringe(budget=budget, rate=0.5),
        create_fringe(budget=budget, rate=0.2)
    ]
    account = budget_f.create_account(parent=budget)
    budget_f.create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        multiplier=1,
        rate=100,
    )
    budget_f.create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=2,
        multiplier=1,
        rate=100,
    )

    api_client.force_login(user)

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['accumulated_fringe_contribution'] == 210.0

    detail_response = api_client.get(
        "/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 210.0

    response = api_client.patch("/v1/fringes/%s/" % fringes[0].pk, data={
        'rate': 0.7
    })
    assert response.status_code == 200

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['accumulated_fringe_contribution'] == 270.0

    detail_response = api_client.get(
        "/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 270.0


def test_caches_invalidated_on_bulk_update_fringes(api_client, user, budget_f,
        create_fringe):
    budget = budget_f.create_budget()
    fringes = [
        create_fringe(budget=budget, rate=0.5),
        create_fringe(budget=budget, rate=0.2)
    ]
    account = budget_f.create_account(parent=budget)
    budget_f.create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        multiplier=1,
        rate=100,
    )
    budget_f.create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=2,
        multiplier=1,
        rate=100,
    )

    api_client.force_login(user)

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['accumulated_fringe_contribution'] == 210.0

    detail_response = api_client.get(
        "/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 210.0

    response = api_client.patch(
        "/v1/%ss/%s/bulk-update-fringes/" % (budget_f.context, budget.pk),
        format='json',
        data={'data': [
            {'id': fringes[0].pk, 'rate': 0.7},
            {'id': fringes[1].pk, 'rate': 0.4}
        ]}
    )
    assert response.status_code == 200

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['accumulated_fringe_contribution'] == 330.0

    detail_response = api_client.get(
        "/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 330.0


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_delete_fringe(api_client, user, budget_f,
        create_fringe):
    budget = budget_f.create_budget()
    fringes = [
        create_fringe(budget=budget, rate=0.5),
        create_fringe(budget=budget, rate=0.2)
    ]
    account = budget_f.create_account(parent=budget)
    budget_f.create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        multiplier=1,
        rate=100,
    )
    budget_f.create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=2,
        multiplier=1,
        rate=100,
    )

    api_client.force_login(user)

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['accumulated_fringe_contribution'] == 210.0

    detail_response = api_client.get(
        "/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 210.0

    response = api_client.delete("/v1/fringes/%s/" % fringes[0].pk)
    assert response.status_code == 204

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['accumulated_fringe_contribution'] == 60.0

    detail_response = api_client.get(
        "/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 60.0


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_bulk_delete_fringes(api_client, user, budget_f,
        create_fringe):
    budget = budget_f.create_budget()
    fringes = [
        create_fringe(budget=budget, rate=0.5),
        create_fringe(budget=budget, rate=0.2)
    ]
    account = budget_f.create_account(parent=budget)
    budget_f.create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=1,
        multiplier=1,
        rate=100,
    )
    budget_f.create_subaccount(
        parent=account,
        fringes=fringes,
        quantity=2,
        multiplier=1,
        rate=100,
    )

    api_client.force_login(user)

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['accumulated_fringe_contribution'] == 210.0

    detail_response = api_client.get(
        "/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 210.0

    response = api_client.patch(
        "/v1/%ss/%s/bulk-delete-fringes/" % (budget_f.context, budget.pk),
        data={'ids': [fringes[0].pk]},
        format='json'
    )
    assert response.status_code == 200

    response = api_client.get(
        "/v1/%ss/%s/children/" % (budget_f.context, budget.pk))
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['accumulated_fringe_contribution'] == 60.0

    detail_response = api_client.get(
        "/v1/%ss/%s/" % (budget_f.context, budget.pk))
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 60.0


@need_to_write
@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_delete_markup():
    pass


@need_to_write
@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_bulk_delete_markups():
    pass


@need_to_write
@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_create_markup():
    pass


@need_to_write
@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_update_markup():
    pass
