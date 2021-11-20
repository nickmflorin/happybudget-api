import pytest
from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_delete(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['id'] == account.pk

    account.delete()
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    # Note: This is kind of a dumb test, because this will return a 404
    # regardless of whether or not the instance was removed from the cache
    # because the Http404 is raised before the .retrieve() method executes.
    assert response.status_code == 404


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_save(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['id'] == account.pk

    response = api_client.patch(
        "/v1/accounts/%s/" % account.pk,
        data={'identifier': '1000'}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['identifier'] == '1000'


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_bulk_save(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['id'] == account.pk

    response = api_client.patch(
        "/v1/%ss/%s/bulk-update-accounts/" % (budget_f.context, budget.pk),
        format='json',
        data={'data': [{'id': account.pk, 'identifier': '1000'}]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['identifier'] == '1000'


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_bulk_delete(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['id'] == account.pk

    response = api_client.patch(
        "/v1/%ss/%s/bulk-delete-accounts/" % (budget_f.context, budget.pk),
        format='json',
        data={'ids': [account.pk]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 404


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_subaccount_delete(api_client, user,
        budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    subaccounts[0].delete()
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [subaccounts[1].pk]


@override_settings(CACHE_ENABLED=True)
def test_detail_cache_invalidated_on_subaccount_create(api_client, user,
        budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    new_subaccount = budget_f.create_subaccount(parent=account)
    response = api_client.get("/v1/accounts/%s/" % account.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [
        s.pk for s in subaccounts] + [new_subaccount.pk]


@override_settings(CACHE_ENABLED=True)
def test_subaccounts_cache_on_search(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    # These subaccounts should not be cached in the response because we will
    # be including a search query parameter.
    budget_f.create_subaccount(parent=account, identifier='Jack')
    budget_f.create_subaccount(parent=account, identifier='Jill')

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200

    response = api_client.get(
        "/v1/accounts/%s/subaccounts/?search=jill" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_fringe_delete(api_client, user, budget_f,
        create_fringe):
    budget = budget_f.create_budget()
    fringes = [create_fringe(budget=budget), create_fringe(budget=budget)]
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account, fringes=fringes),
        budget_f.create_subaccount(parent=account, fringes=fringes)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]

    fringes[0].delete()

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [fringes[1].pk]
    assert response.json()['data'][1]['fringes'] == [fringes[1].pk]

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.json()['fringes'] == [fringes[1].pk]


@override_settings(CACHE_ENABLED=True)
def test_caches_invalidated_on_fringe_create(api_client, user, budget_f,
        create_fringe):
    budget = budget_f.create_budget()
    fringes = [create_fringe(budget=budget), create_fringe(budget=budget)]
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account, fringes=fringes),
        budget_f.create_subaccount(parent=account, fringes=fringes)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]

    new_fringe = create_fringe(budget=budget)
    subaccounts[0].fringes.add(new_fringe)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [
        f.pk for f in fringes] + [new_fringe.pk]
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.json()['fringes'] == [
        f.pk for f in fringes] + [new_fringe.pk]


@override_settings(CACHE_ENABLED=True)
def test_subaccounts_cache_invalidated_on_delete(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.delete("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert response.status_code == 204

    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
def test_subaccounts_cache_invalidated_on_bulk_delete(api_client, user,
        budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/accounts/%s/bulk-delete-subaccounts/" % account.pk,
        format='json',
        data={'ids': [subaccounts[0].pk]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
def test_subaccounts_cache_invalidated_on_create(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    budget_f.create_subaccount(parent=account)
    budget_f.create_subaccount(parent=account)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.post(
        "/v1/accounts/%s/subaccounts/" % account.pk,
        data={"identifier": "1000"}
    )
    assert response.status_code == 201

    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 3


@override_settings(CACHE_ENABLED=True)
def test_subaccounts_cache_invalidated_on_bulk_create(api_client, user,
        budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)

    budget_f.create_subaccount(parent=account)
    budget_f.create_subaccount(parent=account)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/accounts/%s/bulk-create-subaccounts/" % account.pk,
        format='json',
        data={"data": [{"identifier": "1000"}]}
    )
    assert response.status_code == 201

    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 3


@pytest.mark.freeze_time('2020-01-01')
@override_settings(CACHE_ENABLED=True)
def test_subaccounts_cache_invalidated_on_change(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/subaccounts/%s/" % subaccounts[0].pk,
        data={"description": "Test"}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['description'] == 'Test'


@pytest.mark.freeze_time('2020-01-01')
@override_settings(CACHE_ENABLED=True)
def test_subaccounts_cache_invalidated_on_bulk_change(api_client, user,
        budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    response = api_client.patch(
        "/v1/accounts/%s/bulk-update-subaccounts/" % account.pk,
        format='json',
        data={'data': [{'id': subaccounts[0].pk, 'description': 'Test'}]}
    )
    assert response.status_code == 200

    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['description'] == 'Test'


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_delete(api_client, user, budget_f,
        create_group):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = create_group(parent=account)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    group.delete()
    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_create(api_client, user, budget_f,
        create_group):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    create_group(parent=account)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    create_group(parent=account)
    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
def test_groups_cache_invalidated_on_change(api_client, user, budget_f,
        create_group):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    group = create_group(parent=account)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200

    group.name = 'Test Name'
    group.save()

    response = api_client.get("/v1/accounts/%s/groups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['name'] == 'Test Name'


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_delete(api_client, user, budget_f,
        create_markup):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]
    markup = create_markup(parent=account, subaccounts=subaccounts)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    markup.delete()
    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_create(api_client, user, budget_f,
        create_markup):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]
    create_markup(parent=account, subaccounts=subaccounts)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    create_markup(parent=account, subaccounts=subaccounts)
    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
def test_markups_cache_invalidated_on_change(api_client, user, budget_f,
        create_markup):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    subaccounts = [
        budget_f.create_subaccount(parent=account),
        budget_f.create_subaccount(parent=account)
    ]
    markup = create_markup(parent=account, subaccounts=subaccounts)

    api_client.force_login(user)
    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200

    markup.description = 'Test Description'
    markup.save()

    response = api_client.get("/v1/accounts/%s/markups/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['description'] == 'Test Description'


@override_settings(CACHE_ENABLED=True, APP_URL="https://api.greenbudget.com")
def test_subaccounts_cache_invalidated_on_upload_attachment(api_client, user,
        create_budget_account, create_budget_subaccount, create_budget,
        test_uploaded_file):
    budget = create_budget()
    account = create_budget_account(parent=budget)
    subaccounts = [
        create_budget_subaccount(parent=account),
        create_budget_subaccount(parent=account)
    ]

    uploaded_file = test_uploaded_file('test.jpeg')

    api_client.force_login(user)

    # Make the first request to the sub accounts endpoint to cache the results.
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    # Upload the attachment
    response = api_client.post(
        "/v1/subaccounts/%s/attachments/" % subaccounts[0].pk,
        data={'file': uploaded_file}
    )
    assert response.status_code == 200

    # Make another request to the sub accounts endpoint to ensure that the
    # results are not cached.
    response = api_client.get("/v1/accounts/%s/subaccounts/" % account.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['attachments'] == [{
        'id': 1,
        'name': 'test.jpeg',
        'extension': 'jpeg',
        'url': 'https://api.greenbudget.com/media/users/1/attachments/test.jpeg'
    }]
