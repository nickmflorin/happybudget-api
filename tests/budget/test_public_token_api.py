import pytest
import uuid


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_with_public_token(api_client, user, create_budget,
        create_public_token):
    budget = create_budget()
    public_token = create_public_token(instance=budget)
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": budget.pk,
        "name": budget.name,
        "updated_at": "2020-01-01 00:00:00",
        "nominal_value": 0.0,
        "accumulated_fringe_contribution": 0.0,
        "accumulated_markup_contribution": 0.0,
        "actual": 0.0,
        "type": "budget",
        "domain": "budget",
        "image": None,
        "is_permissioned": False,
        "public_token": {
            'id': public_token.pk,
            'created_at': '2020-01-01 00:00:00',
            'public_id': str(public_token.public_id),
            'expires_at': None,
            'is_expired': False
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_public_token(api_client, user, create_budget, models,
        create_public_token):
    budget = create_budget()

    # Create another public token so for another budget to make sure we can
    # share multiple budgets without unique validation errors.
    another_budget = create_budget()
    create_public_token(instance=another_budget)

    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/public-token/" % budget.pk, data={
        'expires_at': '2021-01-01',
    })
    assert response.status_code == 201

    public_token = models.PublicToken.objects.first()
    assert public_token is not None
    assert response.json() == {
        'id': public_token.pk,
        'created_at': '2020-01-01 00:00:00',
        'public_id': str(public_token.public_id),
        'expires_at': '2021-01-01 00:00:00',
        'is_expired': False
    }



@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_public_token_with_uuid(api_client, user, create_budget,
        models):
    budget = create_budget()
    api_client.force_login(user)

    public_id = str(uuid.uuid4())
    response = api_client.post("/v1/budgets/%s/public-token/" % budget.pk, data={
        'expires_at': '2021-01-01',
        'public_id': public_id
    })
    assert response.status_code == 201

    public_token = models.PublicToken.objects.first()
    assert public_token is not None
    assert response.json() == {
        'id': public_token.pk,
        'created_at': '2020-01-01 00:00:00',
        'public_id': str(public_id),
        'expires_at': '2021-01-01 00:00:00',
        'is_expired': False
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_public_token_with_existing_uuid(api_client, user,
        create_budget, create_public_token):
    budget = create_budget()
    another_budget = create_budget()
    api_client.force_login(user)
    public_token = create_public_token(instance=another_budget)

    response = api_client.post("/v1/budgets/%s/public-token/" % budget.pk, data={
        'expires_at': '2021-01-01',
        'public_id': str(public_token.public_id)
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_public_token_with_invalid_uuid(api_client, user,
        create_budget):
    budget = create_budget()
    api_client.force_login(user)

    response = api_client.post("/v1/budgets/%s/public-token/" % budget.pk, data={
        'expires_at': '2021-01-01',
        'public_id': 'jasdlfkj'
    })
    assert response.status_code == 400


@pytest.mark.freeze_time('2020-01-01')
def test_create_another_budget_public_token(api_client, user, create_budget,
        models, create_public_token):
    budget = create_budget()
    create_public_token(instance=budget)
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/public-token/" % budget.pk, data={
        'expires_at': '2021-01-01',
    })
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'Public token already exists for instance.',
        'code': 'unique',
        'error_type': 'global'
    }]}
    assert models.PublicToken.objects.count() == 1
