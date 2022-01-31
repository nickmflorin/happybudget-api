import pytest
import uuid


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_share_token(api_client, user, create_budget,
        create_share_token):
    budget = create_budget()
    share_token = create_share_token(instance=budget)
    api_client.force_login(user)
    response = api_client.get("/v1/auth/share-tokens/%s/" % share_token.pk)
    assert response.status_code == 200
    assert response.json() == {
        'id': share_token.pk,
        'created_at': '2020-01-01 00:00:00',
        'public_id': str(share_token.public_id),
        'expires_at': None,
        'is_expired': False
    }


@pytest.mark.freeze_time('2020-01-01')
def test_delete_budget_share_token(api_client, user, create_budget, models,
        create_share_token):
    budget = create_budget()
    share_token = create_share_token(instance=budget)
    api_client.force_login(user)
    response = api_client.delete("/v1/auth/share-tokens/%s/" % share_token.pk)
    assert response.status_code == 204

    share_token = models.ShareToken.objects.first()
    assert share_token is None


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget_share_token_expiry(api_client, user, create_budget,
        create_share_token):
    budget = create_budget()
    share_token = create_share_token(instance=budget)
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/auth/share-tokens/%s/" % share_token.pk,
        data={'expires_at': '2021-12-12'}
    )
    assert response.status_code == 200
    assert response.json() == {
        'id': share_token.pk,
        'created_at': '2020-01-01 00:00:00',
        'public_id': str(share_token.public_id),
        'expires_at': "2021-12-12 00:00:00",
        'is_expired': False
    }


@pytest.mark.freeze_time('2020-01-01')
def test_update_budget_share_token_public_id(api_client, user, create_budget,
        create_share_token):
    budget = create_budget()
    share_token = create_share_token(instance=budget)
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/auth/share-tokens/%s/" % share_token.pk,
        data={'public_id': str(uuid.uuid4())}
    )
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'This field cannot be updated.',
        'code': 'invalid',
        'error_type': 'field',
        'field': 'public_id'
    }]}
