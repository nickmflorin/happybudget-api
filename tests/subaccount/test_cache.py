from django.test import override_settings
from tests import need_to_write


@override_settings(CACHE_ENABLED=True)
def test_caches_on_search(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)

    # These subaccounts should not be cached in the response because we will
    # be including a search query parameter.
    budget_f.create_subaccount(parent=subaccount, identifier='Jack')
    budget_f.create_subaccount(parent=subaccount, identifier='Jill')

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200

    response = api_client.get(
        "/v1/subaccounts/%s/subaccounts/?search=jill" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True, APP_URL="https://api.greenbudget.com")
def test_caches_invalidated_on_upload_attachment(api_client, user,
        create_budget_account, create_budget_subaccount, create_budget,
        test_uploaded_file):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccount = create_budget_subaccount(parent=account)
    subaccounts = [
        create_budget_subaccount(parent=subaccount),
        create_budget_subaccount(parent=subaccount)
    ]

    uploaded_file = test_uploaded_file('test.jpeg')

    api_client.force_login(user)

    # Make the first request to the sub accounts endpoints to cache the results.
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['attachments'] == []

    response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert response.status_code == 200
    assert response.json()['id'] == subaccounts[0].pk
    assert response.json()['attachments'] == []

    # Upload the attachment
    response = api_client.post(
        "/v1/subaccounts/%s/attachments/" % subaccounts[0].pk,
        data={'file': uploaded_file}
    )
    assert response.status_code == 200

    # Make another request to the sub accounts endpoints to ensure that the
    # results are not cached.
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['attachments'] == [{
        'id': 1,
        'name': 'test.jpeg',
        'extension': 'jpeg',
        'url': 'https://api.greenbudget.com/media/users/1/attachments/test.jpeg'
    }]

    response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert response.status_code == 200
    assert response.json()['id'] == subaccounts[0].pk
    assert response.json()['attachments'] == [{
        'id': 1,
        'name': 'test.jpeg',
        'extension': 'jpeg',
        'url': 'https://api.greenbudget.com/media/users/1/attachments/test.jpeg'
    }]


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_delete(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=subaccount),
        budget_f.create_subaccount(parent=subaccount)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['id'] == subaccount.pk
    assert response.json()['children'] == [s.pk for s in subaccounts]

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert response.status_code == 200

    response = api_client.delete("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert response.status_code == 204

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['id'] == subaccount.pk
    assert response.json()['children'] == [subaccounts[1].pk]

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    # Note: This is kind of a dumb test, because this will return a 404
    # regardless of whether or not the instance was removed from the cache
    # because the Http404 is raised before the .retrieve() method executes.
    assert response.status_code == 404


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_update(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=subaccount),
        budget_f.create_subaccount(parent=subaccount)
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['identifier'] == subaccounts[0].identifier

    response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert response.status_code == 200
    assert response.json()['id'] == subaccounts[0].pk
    assert response.json()['identifier'] == subaccounts[0].identifier

    response = api_client.patch("/v1/subaccounts/%s/" % subaccounts[0].pk, data={
        'identifier': '1000'
    })
    assert response.status_code == 200

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['identifier'] == '1000'

    response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert response.status_code == 200
    assert response.json()['id'] == subaccounts[0].pk
    assert response.json()['identifier'] == '1000'


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_create(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=subaccount),
        budget_f.create_subaccount(parent=subaccount)
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.post(
        "/v1/subaccounts/%s/subaccounts/" % subaccount.pk,
        data={'identifier': '1000'}
    )
    assert response.status_code == 201
    created_id = response.json()['id']

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [
        s.pk for s in subaccounts] + [created_id]

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 3


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_bulk_create(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(parent=subaccount),
        budget_f.create_subaccount(parent=subaccount)
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/subaccounts/%s/bulk-create-subaccounts/" % subaccount.pk,
        format='json',
        data={'data': [{'identifier': '1000'}]}
    )
    assert response.status_code == 201
    created_id = response.json()['children'][0]['id']

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [
        s.pk for s in subaccounts] + [created_id]

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
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
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(
            parent=subaccount,
            fringes=fringes,
            quantity=1,
            multiplier=1,
            rate=100,
        ),
        budget_f.create_subaccount(
            parent=subaccount,
            fringes=fringes,
            quantity=2,
            multiplier=1,
            rate=100,
        )
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][0]['fringe_contribution'] == 70.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 70.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 210.0

    new_fringe = create_fringe(budget=budget, rate=0.5)
    subaccounts[0].fringes.add(new_fringe)

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [
        f.pk for f in fringes] + [new_fringe.pk]
    assert response.json()['data'][0]['fringe_contribution'] == 120.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [
        f.pk for f in fringes] + [new_fringe.pk]
    assert detail_response.json()['fringe_contribution'] == 120.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
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
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(
            parent=subaccount,
            fringes=fringes,
            quantity=1,
            multiplier=1,
            rate=100,
        ),
        budget_f.create_subaccount(
            parent=subaccount,
            fringes=fringes,
            quantity=2,
            multiplier=1,
            rate=100,
        )
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][0]['fringe_contribution'] == 70.0
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][1]['fringe_contribution'] == 140.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 70.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[1].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 140.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 210.0

    response = api_client.patch("/v1/fringes/%s/" % fringes[0].pk, data={
        'rate': 0.7
    })
    assert response.status_code == 200

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][0]['fringe_contribution'] == 90.0
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][1]['fringe_contribution'] == 180.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 90.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[1].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 180.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
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
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(
            parent=subaccount,
            fringes=fringes,
            quantity=1,
            multiplier=1,
            rate=100,
        ),
        budget_f.create_subaccount(
            parent=subaccount,
            fringes=fringes,
            quantity=2,
            multiplier=1,
            rate=100,
        )
    ]

    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][0]['fringe_contribution'] == 70.0
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][1]['fringe_contribution'] == 140.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 70.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[1].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 140.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
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

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][0]['fringe_contribution'] == 110.0
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][1]['fringe_contribution'] == 220.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 110.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[1].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 220.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
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
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(
            parent=subaccount,
            fringes=fringes,
            quantity=1,
            multiplier=1,
            rate=100,
        ),
        budget_f.create_subaccount(
            parent=subaccount,
            fringes=fringes,
            quantity=2,
            multiplier=1,
            rate=100,
        )
    ]
    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][0]['fringe_contribution'] == 70.0
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][1]['fringe_contribution'] == 140.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 70.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[1].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 140.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 210.0

    response = api_client.delete("/v1/fringes/%s/" % fringes[0].pk)
    assert response.status_code == 204

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [fringes[1].pk]
    assert response.json()['data'][0]['fringe_contribution'] == 20.0
    assert response.json()['data'][1]['fringes'] == [fringes[1].pk]
    assert response.json()['data'][1]['fringe_contribution'] == 40.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [fringes[1].pk]
    assert detail_response.json()['fringe_contribution'] == 20.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[1].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [fringes[1].pk]
    assert detail_response.json()['fringe_contribution'] == 40.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
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
    subaccount = budget_f.create_subaccount(parent=account)
    subaccounts = [
        budget_f.create_subaccount(
            parent=subaccount,
            fringes=fringes,
            quantity=1,
            multiplier=1,
            rate=100,
        ),
        budget_f.create_subaccount(
            parent=subaccount,
            fringes=fringes,
            quantity=2,
            multiplier=1,
            rate=100,
        )
    ]
    api_client.force_login(user)

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][0]['fringe_contribution'] == 70.0
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][1]['fringe_contribution'] == 140.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 70.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[1].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]
    assert detail_response.json()['fringe_contribution'] == 140.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['accumulated_fringe_contribution'] == 210.0

    response = api_client.patch(
        "/v1/%ss/%s/bulk-delete-fringes/" % (budget_f.context, budget.pk),
        data={'ids': [fringes[0].pk]},
        format='json'
    )
    assert response.status_code == 200

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [fringes[1].pk]
    assert response.json()['data'][0]['fringe_contribution'] == 20.0
    assert response.json()['data'][1]['fringes'] == [fringes[1].pk]
    assert response.json()['data'][1]['fringe_contribution'] == 40.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [fringes[1].pk]
    assert detail_response.json()['fringe_contribution'] == 20.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[1].pk)
    assert detail_response.status_code == 200
    assert detail_response.json()['fringes'] == [fringes[1].pk]
    assert detail_response.json()['fringe_contribution'] == 40.0

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
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
