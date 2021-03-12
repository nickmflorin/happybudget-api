import pytest


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_comment(api_client, user, create_comment, create_budget):
    budget = create_budget()
    comment = create_comment(user=user, content_object=budget)
    api_client.force_login(user)
    response = api_client.get("/v1/comments/%s/" % comment.pk)
    assert response.status_code == 200
    assert response.json() == {
        'id': comment.pk,
        'created_at': '2020-01-01 00:00:00',
        'updated_at': '2020-01-01 00:00:00',
        'text': comment.text,
        'object_id': budget.pk,
        'likes': [],
        'content_object_type': 'budget',
        'user': {
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'email': user.email
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_account_comment(api_client, user, create_comment, create_account):
    account = create_account()
    comment = create_comment(user=user, content_object=account)
    api_client.force_login(user)
    response = api_client.get("/v1/comments/%s/" % comment.pk)
    assert response.status_code == 200
    assert response.json() == {
        'id': comment.pk,
        'created_at': '2020-01-01 00:00:00',
        'updated_at': '2020-01-01 00:00:00',
        'text': comment.text,
        'object_id': account.pk,
        'likes': [],
        'content_object_type': 'account',
        'user': {
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'email': user.email
        }
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount_comment(api_client, user, create_comment,
        create_sub_account):
    sub_account = create_sub_account()
    comment = create_comment(user=user, content_object=sub_account)
    api_client.force_login(user)
    response = api_client.get("/v1/comments/%s/" % comment.pk)
    assert response.status_code == 200
    assert response.json() == {
        'id': comment.pk,
        'created_at': '2020-01-01 00:00:00',
        'updated_at': '2020-01-01 00:00:00',
        'text': comment.text,
        'object_id': sub_account.pk,
        'likes': [],
        'content_object_type': 'subaccount',
        'user': {
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'email': user.email
        }
    }
