from django.test import override_settings


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
