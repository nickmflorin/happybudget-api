import datetime
import pytest


def test_validate_public_token(api_client, create_public_token, create_budget):
    budget = create_budget()
    public_token = create_public_token(instance=budget)
    response = api_client.post(
        "/v1/auth/validate-public/",
        format='json',
        data={
            'token': public_token.public_id,
            'instance': {'type': 'budget', 'id': budget.pk}
        }
    )
    assert response.status_code == 201
    assert response.json() == {'token_id': str(public_token.private_id)}


def test_validate_public_token_no_token(api_client, create_budget):
    budget = create_budget()
    response = api_client.post(
        "/v1/auth/validate-public/",
        format='json',
        data={'instance': {'type': 'budget', 'id': budget.pk}}
    )
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_validate_public_token_expired_token(api_client, create_public_token,
        create_budget):
    budget = create_budget()
    expires_at = (
        datetime.datetime.now() - datetime.timedelta(days=1)
    ).replace(tzinfo=datetime.timezone.utc)
    public_token = create_public_token(instance=budget, expires_at=expires_at)
    response = api_client.post(
        "/v1/auth/validate-public/",
        format='json',
        data={
            'token': public_token.public_id,
            'instance': {'type': 'budget', 'id': budget.pk}
        }
    )
    assert response.status_code == 401
    assert response.json() == {'errors': [{
        'message': 'Token is expired.',
        'code': 'token_expired',
        'error_type': 'auth'
    }]}


def test_validate_public_token_invalid_token(api_client, create_budget):
    budget = create_budget()
    response = api_client.post(
        "/v1/auth/validate-public/",
        format='json',
        data={
            'token': 'hoopla',
            'instance': {'type': 'budget', 'id': budget.pk}
        }
    )
    assert response.status_code == 400


def test_validate_public_token_invalid_instance(api_client, create_budget,
        create_public_token):
    budget = create_budget()
    another_budget = create_budget()
    public_token = create_public_token(instance=budget)
    response = api_client.post(
        "/v1/auth/validate-public/",
        format='json',
        data={
            'token': public_token.public_id,
            'instance': {'type': 'budget', 'id': another_budget.pk}
        }
    )
    assert response.status_code == 401
    assert response.json() == {'errors': [{
        'message': 'Token is invalid.',
        'code': 'token_not_valid',
        'error_type': 'auth'
    }]}


def test_validate_public_token_non_existent_instance(api_client, create_budget,
        create_public_token):
    budget = create_budget()
    public_token = create_public_token(instance=budget)
    response = api_client.post(
        "/v1/auth/validate-public/",
        format='json',
        data={
            'token': public_token.public_id,
            'instance': {'type': 'budget', 'id': '5'}
        }
    )
    assert response.status_code == 401
    assert response.json() == {'errors': [{
        'message': 'Token is invalid.',
        'code': 'token_not_valid',
        'error_type': 'auth'
    }]}
