import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_public_token(api_client, user, create_budget,
        create_public_token):
    budget = create_budget()
    public_token = create_public_token(instance=budget)
    api_client.force_login(user)
    response = api_client.get("/v1/auth/public-tokens/%s/" % public_token.pk)
    assert response.status_code == 200
    assert response.json() == {
        'id': public_token.pk,
        'created_at': '2020-01-01 00:00:00',
        'public_id': str(public_token.public_id),
        'expires_at': None,
        'is_expired': False
    }


@pytest.mark.freeze_time('2020-01-01')
def test_delete_budget_public_token(api_client, user, create_budget, models,
        create_public_token):
    budget = create_budget()
    public_token = create_public_token(instance=budget)
    api_client.force_login(user)
    response = api_client.delete("/v1/auth/public-tokens/%s/" % public_token.pk)
    assert response.status_code == 204

    public_token = models.PublicToken.objects.first()
    assert public_token is None


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget_public_token_expiry(api_client, user, create_budget,
        create_public_token):
    budget = create_budget()
    public_token = create_public_token(instance=budget)
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/auth/public-tokens/%s/" % public_token.pk,
        data={'expires_at': '2021-12-12'}
    )
    assert response.status_code == 200
    assert response.json() == {
        'id': public_token.pk,
        'created_at': '2020-01-01 00:00:00',
        'public_id': str(public_token.public_id),
        'expires_at': "2021-12-12 00:00:00",
        'is_expired': False
    }
