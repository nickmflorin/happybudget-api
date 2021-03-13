import pytest

from greenbudget.app.comment.models import Comment


@pytest.mark.freeze_time('2020-01-01')
def test_get_budget_comment(api_client, user, create_comment, create_budget):
    budget = create_budget()
    comment = create_comment(user=user, content_object=budget)
    nested_comment = create_comment(content_object=comment, user=user)
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
        },
        'comments': [{
            'id': nested_comment.pk,
            'created_at': '2020-01-01 00:00:00',
            'updated_at': '2020-01-01 00:00:00',
            'text': nested_comment.text,
            'object_id': comment.pk,
            'likes': [],
            'comments': [],
            'content_object_type': 'comment',
            'user': {
                'id': user.pk,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.full_name,
                'email': user.email
            }
        }]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_account_comment(api_client, user, create_comment, create_account):
    account = create_account()
    comment = create_comment(user=user, content_object=account)
    nested_comment = create_comment(content_object=comment, user=user)
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
        },
        'comments': [{
            'id': nested_comment.pk,
            'created_at': '2020-01-01 00:00:00',
            'updated_at': '2020-01-01 00:00:00',
            'text': nested_comment.text,
            'object_id': comment.pk,
            'likes': [],
            'comments': [],
            'content_object_type': 'comment',
            'user': {
                'id': user.pk,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.full_name,
                'email': user.email
            }
        }]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_get_subaccount_comment(api_client, user, create_comment,
        create_sub_account):
    sub_account = create_sub_account()
    comment = create_comment(user=user, content_object=sub_account)
    nested_comment = create_comment(content_object=comment, user=user)
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
        },
        'comments': [{
            'id': nested_comment.pk,
            'created_at': '2020-01-01 00:00:00',
            'updated_at': '2020-01-01 00:00:00',
            'text': nested_comment.text,
            'object_id': comment.pk,
            'likes': [],
            'comments': [],
            'content_object_type': 'comment',
            'user': {
                'id': user.pk,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.full_name,
                'email': user.email
            }
        }]
    }


@pytest.mark.freeze_time('2020-01-01')
def test_create_budget_comment(api_client, user, create_budget):
    budget = create_budget()
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/comments/" % budget.pk, data={
        "text": "This is a fake comment."
    })
    assert response.status_code == 201
    assert response.json() == {
        'id': 1,
        'created_at': '2020-01-01 00:00:00',
        'updated_at': '2020-01-01 00:00:00',
        'text': "This is a fake comment.",
        'object_id': budget.pk,
        'likes': [],
        'comments': [],
        'content_object_type': 'budget',
        'user': {
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'email': user.email
        }
    }
    comment = Comment.objects.first()
    assert comment is not None
    assert comment.text == "This is a fake comment."
    assert comment.content_object == budget
    assert comment.user == user


@pytest.mark.freeze_time('2020-01-01')
def test_create_account_comment(api_client, user, create_budget, create_account):  # noqa
    budget = create_budget()
    account = create_account(budget=budget)
    api_client.force_login(user)
    response = api_client.post("/v1/accounts/%s/comments/" % account.pk, data={
        "text": "This is a fake comment."
    })
    assert response.status_code == 201
    assert response.json() == {
        'id': 1,
        'created_at': '2020-01-01 00:00:00',
        'updated_at': '2020-01-01 00:00:00',
        'text': "This is a fake comment.",
        'object_id': account.pk,
        'likes': [],
        'comments': [],
        'content_object_type': 'account',
        'user': {
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'email': user.email
        }
    }
    comment = Comment.objects.first()
    assert comment is not None
    assert comment.text == "This is a fake comment."
    assert comment.content_object == account
    assert comment.user == user


@pytest.mark.freeze_time('2020-01-01')
def test_create_sub_account_comment(api_client, user, create_budget,
        create_account, create_sub_account):
    budget = create_budget()
    account = create_account(budget=budget)
    subaccount = create_sub_account(parent=account, budget=budget)
    api_client.force_login(user)
    response = api_client.post(
        "/v1/subaccounts/%s/comments/" % subaccount.pk,
        data={"text": "This is a fake comment."}
    )
    assert response.status_code == 201
    assert response.json() == {
        'id': 1,
        'created_at': '2020-01-01 00:00:00',
        'updated_at': '2020-01-01 00:00:00',
        'text': "This is a fake comment.",
        'object_id': subaccount.pk,
        'likes': [],
        'comments': [],
        'content_object_type': 'subaccount',
        'user': {
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'email': user.email
        }
    }
    comment = Comment.objects.first()
    assert comment is not None
    assert comment.text == "This is a fake comment."
    assert comment.content_object == subaccount
    assert comment.user == user


@pytest.mark.freeze_time('2020-01-01')
def test_reply_to_comment(api_client, user, create_comment, create_budget):
    budget = create_budget()
    comment = create_comment(user=user, content_object=budget)

    api_client.force_login(user)
    response = api_client.post("/v1/comments/%s/reply/" % comment.pk, data={
        'text': 'This is a reply!'
    })
    assert response.status_code == 201

    comment.refresh_from_db()
    assert comment.comments.count() == 1

    nested_comment = comment.comments.first()
    assert response.json() == {
        'id': nested_comment.pk,
        'created_at': '2020-01-01 00:00:00',
        'updated_at': '2020-01-01 00:00:00',
        'text': nested_comment.text,
        'object_id': comment.pk,
        'likes': [],
        'comments': [],
        'content_object_type': 'comment',
        'user': {
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'email': user.email
        }
    }
