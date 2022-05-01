import pytest

from greenbudget.app.collaborator.models import Collaborator


@pytest.mark.freeze_time('2020-01-01')
def test_get_collaborators_as_owner(api_client, user, models, f):
    budget = f.create_budget()
    additional_users = [f.create_user(), f.create_user()]
    collaborators = [
        f.create_collaborator(user=additional_users[0], instance=budget),
        f.create_collaborator(user=additional_users[1], instance=budget),
    ]
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/collaborators/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [
        {
            'id': collaborators[0].pk,
            'type': 'collaborator',
            'created_at': '2020-01-01 00:00:00',
            'updated_at': '2020-01-01 00:00:00',
            'access_type': {
                'id': collaborators[0].access_type,
                'name': models.Collaborator.ACCESS_TYPES[
                    collaborators[0].access_type].name,
                'slug': models.Collaborator.ACCESS_TYPES[
                    collaborators[0].access_type].slug,
            },
            'user': {
                'id': additional_users[0].pk,
                'first_name': additional_users[0].first_name,
                'last_name': additional_users[0].last_name,
                'full_name': additional_users[0].full_name,
                'email': additional_users[0].email,
                'profile_image': None
            }
        },
        {
            'id': collaborators[1].pk,
            'type': 'collaborator',
            'created_at': '2020-01-01 00:00:00',
            'updated_at': '2020-01-01 00:00:00',
            'access_type': {
                'id': collaborators[1].access_type,
                'name': models.Collaborator.ACCESS_TYPES[
                    collaborators[1].access_type].name,
                'slug': models.Collaborator.ACCESS_TYPES[
                    collaborators[1].access_type].slug,
            },
            'user': {
                'id': additional_users[1].pk,
                'first_name': additional_users[1].first_name,
                'last_name': additional_users[1].last_name,
                'full_name': additional_users[1].full_name,
                'email': additional_users[1].email,
                'profile_image': None
            }
        }
    ]


@pytest.mark.parametrize('access_type', [
    Collaborator.ACCESS_TYPES.owner,
    Collaborator.ACCESS_TYPES.editor,
    Collaborator.ACCESS_TYPES.view_only,
])
def test_get_collaborators_as_collaborator(api_client, access_type, f):
    budget = f.create_budget()
    users = [f.create_user(), f.create_user()]
    _ = [
        f.create_collaborator(
            user=users[0],
            instance=budget,
            access_type=access_type
        ),
        f.create_collaborator(user=users[1], instance=budget),
    ]
    api_client.force_login(users[0])
    response = api_client.get("/v1/budgets/%s/collaborators/" % budget.pk)
    assert response.status_code == 200


@pytest.mark.freeze_time('2020-01-01')
def test_create_collaborator_as_owner(api_client, user, models, f):
    budget = f.create_budget()
    collaborating_user = f.create_user()
    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/collaborators/" % budget.pk,
        data={
            'user': collaborating_user.pk,
            'access_type': models.Collaborator.ACCESS_TYPES.editor
        }
    )
    assert response.status_code == 201
    assert models.Collaborator.objects.count() == 1
    collaborator = models.Collaborator.objects.first()

    assert response.json() == {
        'id': collaborator.pk,
        'type': 'collaborator',
        'created_at': '2020-01-01 00:00:00',
        'updated_at': '2020-01-01 00:00:00',
        'access_type': {
            'id': models.Collaborator.ACCESS_TYPES.editor,
            'name': models.Collaborator.ACCESS_TYPES[
                models.Collaborator.ACCESS_TYPES.editor].name,
            'slug': models.Collaborator.ACCESS_TYPES[
                models.Collaborator.ACCESS_TYPES.editor].slug
        },
        'user': {
            'id': collaborating_user.pk,
            'first_name': collaborating_user.first_name,
            'last_name': collaborating_user.last_name,
            'full_name': collaborating_user.full_name,
            'email': collaborating_user.email,
            'profile_image': None
        }
    }


def test_assign_self_as_collaborator(api_client, f, user, models):
    budget = f.create_budget(created_by=user)
    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/collaborators/" % budget.pk,
        data={
            'user': user.pk,
            'access_type': models.Collaborator.ACCESS_TYPES.editor
        }
    )
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'A user cannot assign themselves as a collaborator.',
        'code': 'invalid',
        'error_type': 'field',
        'field': 'user'
    }]}


def test_assign_owner_as_collaborator(api_client, f, user, models):
    owner = f.create_user()
    budget = f.create_budget(created_by=owner)
    # Since we are not submitting the request as the owner of the budget, we
    # must submit it as a collaborator with the owner access type.
    f.create_collaborator(instance=budget, user=user, owner=True)
    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/collaborators/" % budget.pk,
        data={
            'user': owner.pk,
            'access_type': models.Collaborator.ACCESS_TYPES.editor
        }
    )
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': (
            f'The user {owner.pk} created the instance and cannot be assigned '
            'as a collaborator.'
        ),
        'code': 'invalid',
        'error_type': 'field',
        'field': 'user'
    }]}


def test_create_duplicate_collaborator(api_client, user, models, f):
    budget = f.create_budget()
    collaborating_user = f.create_user()
    f.create_collaborator(
        user=collaborating_user,
        instance=budget,
        owner=True
    )
    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/collaborators/" % budget.pk,
        data={
            'user': collaborating_user.pk,
            'access_type': models.Collaborator.ACCESS_TYPES.editor
        }
    )
    assert response.status_code == 400
    assert response.json() == {'errors': [{
        'message': 'The user is already a collaborator.',
        'code': 'unique',
        'error_type': 'field',
        'field': 'user'
    }]}


@pytest.mark.freeze_time('2020-01-01')
def test_create_collaborator_as_collaborating_owner(api_client, models, f):
    budget = f.create_budget()
    collaborating_user = f.create_user()
    f.create_collaborator(
        user=collaborating_user,
        instance=budget,
        owner=True
    )
    another_collaborating_user = f.create_user()
    api_client.force_login(collaborating_user)
    response = api_client.post(
        "/v1/budgets/%s/collaborators/" % budget.pk,
        data={
            'user': another_collaborating_user.pk,
            'access_type': models.Collaborator.ACCESS_TYPES.editor
        }
    )
    assert response.status_code == 201
    assert models.Collaborator.objects.count() == 2
    collaborator = models.Collaborator.objects.all()[1]

    assert response.json() == {
        'id': collaborator.pk,
        'type': 'collaborator',
        'created_at': '2020-01-01 00:00:00',
        'updated_at': '2020-01-01 00:00:00',
        'access_type': {
            'id': models.Collaborator.ACCESS_TYPES.editor,
            'name': models.Collaborator.ACCESS_TYPES[
                models.Collaborator.ACCESS_TYPES.editor].name,
            'slug': models.Collaborator.ACCESS_TYPES[
                models.Collaborator.ACCESS_TYPES.editor].slug
        },
        'user': {
            'id': another_collaborating_user.pk,
            'first_name': another_collaborating_user.first_name,
            'last_name': another_collaborating_user.last_name,
            'full_name': another_collaborating_user.full_name,
            'email': another_collaborating_user.email,
            'profile_image': None
        }
    }


@pytest.mark.parametrize('access_type', [
    Collaborator.ACCESS_TYPES.editor,
    Collaborator.ACCESS_TYPES.view_only,
])
def test_create_collaborator_as_non_owner_collaborator(api_client, access_type,
        models, f):
    budget = f.create_budget()
    collaborating_user = f.create_user()
    f.create_collaborator(
        user=collaborating_user,
        instance=budget,
        access_type=access_type
    )
    another_collaborating_user = f.create_user()
    api_client.force_login(collaborating_user)
    response = api_client.post(
        "/v1/budgets/%s/collaborators/" % budget.pk,
        data={
            'user': another_collaborating_user.pk,
            'access_type': models.Collaborator.ACCESS_TYPES.editor
        }
    )
    assert response.status_code == 403
    assert response.json() == {'errors': [{
        'message': (
            'The user is a collaborator for this budget but does not have the '
            'correct access type.'
        ),
        'code': 'permission_error',
        'error_type': 'permission'
    }]}


def test_create_collaborator_as_non_owner_non_collaborator(api_client, f, user,
        models):
    owner = f.create_user()
    budget = f.create_budget(created_by=owner)
    collaborating_user = f.create_user()
    api_client.force_login(user)
    response = api_client.post(
        "/v1/budgets/%s/collaborators/" % budget.pk,
        data={
            'user': collaborating_user.pk,
            'access_type': models.Collaborator.ACCESS_TYPES.editor
        }
    )
    assert response.status_code == 403
    assert response.json() == {'errors': [{
        'message': 'The user is not a collaborator for this budget.',
        'code': 'permission_error',
        'error_type': 'permission'
    }]}
