import pytest
from django.test import override_settings


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_detail_cache_invalidated_on_delete(api_client, user, context,
        create_subaccount, create_account, create_context_budget):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['id'] == subaccount.pk

    subaccount.delete()
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    # Note: This is kind of a dumb test, because this will return a 404
    # regardless of whether or not the instance was removed from the cache
    # because the Http404 is raised before the .retrieve() method executes.
    assert response.status_code == 404


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_detail_cache_invalidated_on_save(api_client, user, context,
        create_subaccount, create_account, create_context_budget):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['id'] == subaccount.pk

    subaccount.identifier = '1000'
    subaccount.save()

    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['identifier'] == '1000'


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_detail_cache_invalidated_on_subaccount_delete(api_client, user,
        context, create_subaccount, create_account, create_context_budget):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)

    subaccounts = [
        create_subaccount(parent=subaccount, context=context),
        create_subaccount(parent=subaccount, context=context)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    subaccounts[0].delete()
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [subaccounts[1].pk]


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_detail_cache_invalidated_on_subaccount_create(api_client, user,
        context, create_subaccount, create_account, create_context_budget):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)

    subaccounts = [
        create_subaccount(parent=subaccount, context=context),
        create_subaccount(parent=subaccount, context=context)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [s.pk for s in subaccounts]

    new_subaccount = create_subaccount(parent=subaccount, context=context)
    response = api_client.get("/v1/subaccounts/%s/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['children'] == [
        s.pk for s in subaccounts] + [new_subaccount.pk]


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_subaccounts_cache_on_search(api_client, user, context,
        create_subaccount, create_account, create_context_budget):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)

    # These subaccounts should not be cached in the response because we will
    # be including a search query parameter.
    create_subaccount(parent=subaccount, context=context, identifier='Jack')
    create_subaccount(parent=subaccount, context=context, identifier='Jill')

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200

    response = api_client.get(
        "/v1/subaccounts/%s/subaccounts/?search=jill" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_caches_invalidated_on_fringes_changed(api_client, user, context,
        create_subaccount, create_account, create_context_budget, create_fringe):
    budget = create_context_budget(context=context)
    fringes = [create_fringe(budget=budget), create_fringe(budget=budget)]
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(parent=subaccount, context=context, fringes=fringes),
        create_subaccount(parent=subaccount, context=context, fringes=fringes)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]

    new_fringe = create_fringe(budget=budget)
    subaccounts[0].fringes.add(new_fringe)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [
        f.pk for f in fringes] + [new_fringe.pk]
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.json()['fringes'] == [
        f.pk for f in fringes] + [new_fringe.pk]


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_caches_invalidated_on_fringe_delete(api_client, user, context,
        create_subaccount, create_account, create_context_budget, create_fringe):
    budget = create_context_budget(context=context)
    fringes = [create_fringe(budget=budget), create_fringe(budget=budget)]
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(parent=subaccount, context=context, fringes=fringes),
        create_subaccount(parent=subaccount, context=context, fringes=fringes)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]

    fringes[0].delete()

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [fringes[1].pk]
    assert response.json()['data'][1]['fringes'] == [fringes[1].pk]

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.json()['fringes'] == [fringes[1].pk]


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_caches_invalidated_on_fringe_create(api_client, user, context,
        create_subaccount, create_account, create_context_budget, create_fringe):
    budget = create_context_budget(context=context)
    fringes = [create_fringe(budget=budget), create_fringe(budget=budget)]
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(parent=subaccount, context=context, fringes=fringes),
        create_subaccount(parent=subaccount, context=context, fringes=fringes)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [f.pk for f in fringes]
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.json()['fringes'] == [f.pk for f in fringes]

    new_fringe = create_fringe(budget=budget)
    subaccounts[0].fringes.add(new_fringe)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['fringes'] == [
        f.pk for f in fringes] + [new_fringe.pk]
    assert response.json()['data'][1]['fringes'] == [f.pk for f in fringes]

    detail_response = api_client.get("/v1/subaccounts/%s/" % subaccounts[0].pk)
    assert detail_response.json()['fringes'] == [
        f.pk for f in fringes] + [new_fringe.pk]


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_subaccounts_cache_invalidated_on_delete(api_client, user, context,
        create_subaccount, create_account, create_context_budget):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(parent=subaccount, context=context),
        create_subaccount(parent=subaccount, context=context)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    subaccounts[0].delete()
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_subaccounts_cache_invalidated_on_create(api_client, user, context,
        create_subaccount, create_account, create_context_budget):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)

    create_subaccount(parent=subaccount, context=context),
    create_subaccount(parent=subaccount, context=context)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    create_subaccount(parent=subaccount, context=context)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 3


@pytest.mark.freeze_time('2020-01-01')
@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_subaccounts_cache_invalidated_on_change(api_client, user, context,
        create_subaccount, create_account, create_context_budget):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(parent=subaccount, context=context),
        create_subaccount(parent=subaccount, context=context)
    ]

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2

    subaccounts[0].description = 'Test Description'
    subaccounts[0].save()

    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['description'] == 'Test Description'


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_groups_cache_invalidated_on_delete(api_client, user, context,
        create_subaccount, create_account, create_context_budget, create_group):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    group = create_group(parent=subaccount)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/groups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    group.delete()
    response = api_client.get("/v1/subaccounts/%s/groups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_groups_cache_invalidated_on_create(api_client, user, context,
        create_subaccount, create_account, create_context_budget, create_group):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    create_group(parent=subaccount)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/groups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    create_group(parent=subaccount)
    response = api_client.get("/v1/subaccounts/%s/groups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_groups_cache_invalidated_on_change(api_client, user, context,
        create_subaccount, create_account, create_context_budget, create_group):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    group = create_group(parent=subaccount)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/groups/" % subaccount.pk)
    assert response.status_code == 200

    group.name = 'Test Name'
    group.save()

    response = api_client.get("/v1/subaccounts/%s/groups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['name'] == 'Test Name'


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_markups_cache_invalidated_on_delete(api_client, user, context,
        create_subaccount, create_account, create_context_budget, create_markup):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(parent=subaccount, context=context),
        create_subaccount(parent=subaccount, context=context)
    ]
    markup = create_markup(parent=subaccount, subaccounts=subaccounts)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/markups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    markup.delete()
    response = api_client.get("/v1/subaccounts/%s/markups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 0


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_markups_cache_invalidated_on_create(api_client, user, context,
        create_subaccount, create_account, create_context_budget, create_markup):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(parent=subaccount, context=context),
        create_subaccount(parent=subaccount, context=context)
    ]
    create_markup(parent=subaccount, subaccounts=subaccounts)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/markups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1

    create_markup(parent=subaccount, subaccounts=subaccounts)
    response = api_client.get("/v1/subaccounts/%s/markups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2


@override_settings(CACHE_ENABLED=True)
@pytest.mark.parametrize('context', ['budget', 'template'])
def test_markups_cache_invalidated_on_change(api_client, user, context,
        create_subaccount, create_account, create_context_budget, create_markup):
    budget = create_context_budget(context=context)
    account = create_account(parent=budget, context=context)
    subaccount = create_subaccount(parent=account, context=context)
    subaccounts = [
        create_subaccount(parent=subaccount, context=context),
        create_subaccount(parent=subaccount, context=context)
    ]
    markup = create_markup(parent=subaccount, subaccounts=subaccounts)

    api_client.force_login(user)
    response = api_client.get("/v1/subaccounts/%s/groups/" % subaccount.pk)
    assert response.status_code == 200

    markup.description = 'Test Description'
    markup.save()

    response = api_client.get("/v1/subaccounts/%s/markups/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['data'][0]['description'] == 'Test Description'


@override_settings(CACHE_ENABLED=True, APP_URL="https://api.greenbudget.com")
def test_subaccounts_cache_invalidated_on_upload_attachment(api_client, user,
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

    # Make the first request to the sub accounts endpoint to cache the results.
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
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
    response = api_client.get("/v1/subaccounts/%s/subaccounts/" % subaccount.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['attachments'] == [{
        'id': 1,
        'name': 'test.jpeg',
        'extension': 'jpeg',
        'url': 'https://api.greenbudget.com/media/users/1/attachments/test.jpeg'
    }]
