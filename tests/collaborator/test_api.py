import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_update_collaborator(api_client, create_collaborator, create_budget,
        user, models):
    budget = create_budget()
    collaborator = create_collaborator(
        user=user,
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
        'access_type': {
            'id': models.Collaborator.ACCESS_TYPES.owner,
            'name': models.Collaborator.ACCESS_TYPES[
                models.Collaborator.ACCESS_TYPES.owner]
        },
        'user': {
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'email': user.email,
            'profile_image': None
        }
    }
    collaborator.refresh_from_db()
    assert collaborator.access_type == models.Collaborator.ACCESS_TYPES.owner


@pytest.mark.freeze_time('2020-01-01')
def test_update_collaborator_user(api_client, create_collaborator, create_budget,
        user, models, create_user):
    budget = create_budget()
    collaborator = create_collaborator(
        user=user,
        instance=budget,
        view_only=True
    )
    api_client.force_login(user)
    another_user = create_user()
    response = api_client.patch(
        "/v1/collaborators/%s/" % collaborator.pk,
        data={'user': another_user.pk}
    )
    # We should not be able to change the user of a collaborator after it is
    # created.
    assert response.status_code == 200
    assert response.json() == {
        'id': collaborator.pk,
        'type': 'collaborator',
        'created_at': '2020-01-01 00:00:00',
        'access_type': {
            'id': collaborator.access_type,
            'name': models.Collaborator.ACCESS_TYPES[collaborator.access_type]
        },
        'user': {
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'email': user.email,
            'profile_image': None
        }
    }
    collaborator.refresh_from_db()
    assert collaborator.user == user


@pytest.mark.freeze_time('2020-01-01')
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


@pytest.mark.freeze_time('2020-01-01')
def test_update_collaborator_as_non_owner_collaborator(api_client, create_user,
        create_collaborator, create_budget, models):
    budget = create_budget()
    collaborating_user = create_user()
    collaborator = create_collaborator(
        user=collaborating_user,
        instance=budget,
        editor=True
    )
    api_client.force_login(collaborating_user)
    response = api_client.patch(
        "/v1/collaborators/%s/" % collaborator.pk,
        data={'access_type': models.Collaborator.ACCESS_TYPES.owner}
    )
    assert response.status_code == 403
