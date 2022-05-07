import datetime
import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_with_public_token(api_client, user, f):
    budget = f.create_budget()
    public_token = f.create_public_token(instance=budget)
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
        "updated_by": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "email": user.email,
            "profile_image": None
        },
        "public_token": {
            'id': public_token.pk,
            'created_at': '2020-01-01 00:00:00',
            'public_id': str(public_token.public_id),
            'expires_at': None,
            'is_expired': False
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_public_token(api_client, user, f, models):
    budget = f.create_budget()

    # Create another public token so for another budget to make sure we can
    # share multiple budgets without unique validation errors.
    another_budget = f.create_budget()
    f.create_public_token(instance=another_budget)

    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/public-token/" % budget.pk, data={
        'expires_at': '2021-01-01',
    })
    assert response.status_code == 201

    public_token = models.PublicToken.objects.all()[1]
    assert public_token is not None
    assert response.json() == {
        'id': public_token.pk,
        'created_at': '2020-01-01 00:00:00',
        'public_id': str(public_token.public_id),
        'expires_at': '2021-01-01 00:00:00',
        'is_expired': False
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_public_token_with_previously_expired(api_client, user,
        f, models):
    budget = f.create_budget()
    # Create a public token for the same budget that has already expired.
    # This should not prevent us from being able to create a public token for
    # the budget.
    f.create_public_token(
        instance=budget,
        expires_at=datetime.datetime(2019, 11, 1).replace(
            tzinfo=datetime.timezone.utc)
    )
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/public-token/" % budget.pk, data={
        'expires_at': '2021-01-01',
    })
    assert response.status_code == 201

    # The previously expired public token should have been deleted.
    assert models.PublicToken.objects.count() == 1

    public_token = models.PublicToken.objects.first()
    assert public_token.expires_at == datetime.datetime(2021, 1, 1).replace(
        tzinfo=datetime.timezone.utc)

    assert response.json() == {
        'id': public_token.pk,
        'created_at': '2020-01-01 00:00:00',
        'public_id': str(public_token.public_id),
        'expires_at': '2021-01-01 00:00:00',
        'is_expired': False
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_another_budget_public_token(api_client, user, models, f):
    budget = f.create_budget()
    f.create_public_token(instance=budget)
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/public-token/" % budget.pk, data={
        'expires_at': '2021-01-01',
    })
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'Public token already exists for instance.',
        'code': 'unique',
        'error_type': 'form'
    }]}
    assert models.PublicToken.objects.count() == 1
