import pytest

from greenbudget.app.collaborator.models import Collaborator


@pytest.mark.freeze_time('2020-01-01')
def test_update_collaborator(api_client, create_collaborator, create_budget,
        user, models, create_user):
    budget = create_budget()
    collaborating_user = create_user()
    collaborator = create_collaborator(
        user=collaborating_user,
        instance=budget,
        view_only=True
    )
    api_client.force_login(user)
    response = api_client.patch(
        "/v1/collaborators/%s/" % collaborator.pk,
        data={'access_type': models.Collaborator.ACCESS_TYPES.owner}
    )
    assert response.status_code == 200
    assert response.json() == {
        'id': collaborator.pk,
        'type': 'collaborator',
        'created_at': '2020-01-01 00:00:00',
        'updated_at': '2020-01-01 00:00:00',
        'access_type': {
            'id': models.Collaborator.ACCESS_TYPES.owner,
            'name': models.Collaborator.ACCESS_TYPES[
                models.Collaborator.ACCESS_TYPES.owner]
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
    collaborator.refresh_from_db()
    assert collaborator.access_type == models.Collaborator.ACCESS_TYPES.owner


def test_delete_collaborator(api_client, create_collaborator, create_budget,
        user, models, create_user):
    budget = create_budget()
    collaborating_user = create_user()
    collaborator = create_collaborator(
        user=collaborating_user,
        instance=budget,
        view_only=True
    )
    api_client.force_login(user)
    response = api_client.delete("/v1/collaborators/%s/" % collaborator.pk)
    assert response.status_code == 204
    assert models.Collaborator.objects.count() == 0


@pytest.mark.freeze_time('2020-01-01')
def test_update_collaborator_user(api_client, create_collaborator, create_budget,
        user, models, create_user):
    budget = create_budget()
    collaborating_user = create_user()
    collaborator = create_collaborator(
        user=collaborating_user,
        instance=budget,
        view_only=True
    )
    api_client.force_login(user)
    another_collaborating_user = create_user(first_name='blah')
    response = api_client.patch(
        "/v1/collaborators/%s/" % collaborator.pk,
        data={'user': another_collaborating_user.pk}
    )
    # We should not be able to change the user of a collaborator after it is
    # created.
    assert response.status_code == 200
    assert response.json() == {
        'id': collaborator.pk,
        'type': 'collaborator',
        'created_at': '2020-01-01 00:00:00',
        'updated_at': '2020-01-01 00:00:00',
        'access_type': {
            'id': collaborator.access_type,
            'name': models.Collaborator.ACCESS_TYPES[collaborator.access_type]
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
    collaborator.refresh_from_db()
    assert collaborator.user == collaborating_user


def test_update_collaborator_as_collaborator(api_client, create_collaborator,
        create_budget, create_user, models):
    budget = create_budget()
    collaborating_user = create_user()
    collaborator = create_collaborator(
        user=collaborating_user,
        instance=budget,
        owner=True
    )
    api_client.force_login(collaborating_user)
    response = api_client.patch(
        "/v1/collaborators/%s/" % collaborator.pk,
        data={'access_type': models.Collaborator.ACCESS_TYPES.owner}
    )
    assert response.status_code == 200


def test_delete_collaborator_as_collaborator(api_client, create_collaborator,
        create_budget, models, create_user):
    budget = create_budget()
    collaborating_user = create_user()
    collaborator = create_collaborator(
        user=collaborating_user,
        instance=budget,
        owner=True
    )
    api_client.force_login(collaborating_user)
    response = api_client.delete("/v1/collaborators/%s/" % collaborator.pk)
    assert response.status_code == 204
    assert models.Collaborator.objects.count() == 0


@pytest.mark.parametrize('access_type', [
    Collaborator.ACCESS_TYPES.editor,
    Collaborator.ACCESS_TYPES.view_only,
])
def test_update_collaborator_as_non_owner_collaborator(api_client, create_user,
        create_collaborator, create_budget, models, access_type):
    budget = create_budget()
    collaborating_user = create_user()
    collaborator = create_collaborator(
        user=collaborating_user,
        instance=budget,
        access_type=access_type
    )
    api_client.force_login(collaborating_user)
    response = api_client.patch(
        "/v1/collaborators/%s/" % collaborator.pk,
        data={'access_type': models.Collaborator.ACCESS_TYPES.owner}
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


@pytest.mark.parametrize('access_type', [
    Collaborator.ACCESS_TYPES.editor,
    Collaborator.ACCESS_TYPES.view_only,
])
def test_delete_collaborator_as_non_owner_collaborator(api_client, access_type,
        create_collaborator, create_budget, create_user):
    budget = create_budget()
    collaborating_user = create_user()
    collaborator = create_collaborator(
        user=collaborating_user,
        instance=budget,
        access_type=access_type
    )
    api_client.force_login(collaborating_user)
    response = api_client.delete("/v1/collaborators/%s/" % collaborator.pk)
    assert response.status_code == 403
    assert response.json() == {'errors': [{
        'message': (
            'The user is a collaborator for this budget but does not have the '
            'correct access type.'
        ),
        'code': 'permission_error',
        'error_type': 'permission'
    }]}
