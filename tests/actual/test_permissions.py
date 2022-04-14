# pylint: disable=redefined-outer-name
import pytest

from greenbudget.app.collaborator.models import Collaborator


@pytest.fixture
def another_user_case(api_client, user, create_user, create_budget,
        create_actual):
    def inner(case_info=None, model_kwargs=None):
        another_user = create_user()
        api_client.force_login(user)
        budget = create_budget(created_by=another_user)
        model_kwargs = model_kwargs or {}
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(budget)
        # Here, the user that created the Actual doesn't really matter, since
        # the ownership is dictated by the Budget.
        return create_actual(budget=budget, **model_kwargs)
    return inner


@pytest.fixture
def public_case(api_client, user, create_budget, create_public_token,
        create_actual):
    def inner(case_info=None, model_kwargs=None):
        budget = create_budget(created_by=user)
        public_token = create_public_token(instance=budget)
        api_client.include_public_token(public_token)
        model_kwargs = model_kwargs or {}
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(budget)
        return create_actual(budget=budget, **model_kwargs)
    return inner


@pytest.fixture
def another_public_case(api_client, user, create_budget, create_actual,
        create_public_token):
    def inner(case_info=None, model_kwargs=None):
        budget = create_budget(created_by=user)
        another_budget = create_budget(created_by=user)
        public_token = create_public_token(instance=another_budget)
        api_client.include_public_token(public_token)
        model_kwargs = model_kwargs or {}
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(budget)
        return create_actual(budget=budget, **model_kwargs)
    return inner


@pytest.fixture
def logged_in_case(api_client, user, create_budget, create_actual):
    def inner(case_info=None, model_kwargs=None):
        budget = create_budget(created_by=user)
        api_client.force_login(user)
        model_kwargs = model_kwargs or {}
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(budget)
        return create_actual(budget=budget, **model_kwargs)
    return inner


@pytest.fixture
def not_logged_in_case(user, create_budget, create_actual):
    def inner(case_info=None, model_kwargs=None):
        budget = create_budget(created_by=user)
        model_kwargs = model_kwargs or {}
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(budget)
        return create_actual(budget=budget, **model_kwargs)
    return inner


@pytest.fixture
def multiple_case(api_client, create_budget, create_actual, user):
    def inner(case_info=None, model_kwargs=None):
        create_budget(created_by=user)
        budget = create_budget(created_by=user)
        model_kwargs = model_kwargs or {}
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(budget)
        actual = create_actual(budget=budget, **model_kwargs)
        if case_info and case_info.get('login', True) is True:
            api_client.force_login(user)
        return actual
    return inner


@pytest.fixture
def collaborator_case(api_client, user, create_user, create_budget,
        create_collaborator, create_actual):
    def inner(case_info, model_kwargs=None):
        budget = create_budget(created_by=user)
        collaborating_user = create_user()
        create_collaborator(
            access_type=case_info['access_type'],
            user=collaborating_user,
            instance=budget
        )
        if case_info and case_info.get('login', True) is True:
            api_client.force_login(collaborating_user)
        model_kwargs = model_kwargs or {}
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(budget)
        return create_actual(budget=budget, **model_kwargs)
    return inner


@pytest.fixture
def establish_case(another_user_case, multiple_case, another_public_case,
        collaborator_case, logged_in_case, not_logged_in_case, public_case):
    def inner(case, model_kwargs=None):
        cases = {
            'another_user': another_user_case,
            'not_logged_in': not_logged_in_case,
            'logged_in': logged_in_case,
            'multiple_budgets': multiple_case,
            'public_case': public_case,
            'another_public_case': another_public_case,
            'collaborator': collaborator_case,
        }
        if isinstance(case, tuple):
            return cases[case[0]](case[1], model_kwargs=model_kwargs)
        return cases[case]({}, model_kwargs=model_kwargs)
    return inner


@pytest.fixture
def update_test_case(api_client, establish_case):
    def inner(data, case):
        actual = establish_case(case)
        return api_client.patch("/v1/actuals/%s/" % actual.pk, data=data)
    return inner


@pytest.fixture
def detail_test_case(api_client, establish_case):
    def inner(case, path="/"):
        actual = establish_case(case)
        url = "/v1/actuals/%s%s" % (actual.pk, path)
        return api_client.get(url)
    return inner


@pytest.fixture
def detail_create_test_case(api_client, establish_case):
    def inner(data, case, path="/"):
        actual = establish_case(case)
        url = "/v1/actuals/%s%s" % (actual.pk, path)
        if hasattr(data, '__call__'):
            data = data(actual)
        return api_client.post(url, data=data)
    return inner


@pytest.fixture
def detail_delete_test_case(api_client, establish_case):
    def inner(case, path="/", model_kwargs=None):
        actual = establish_case(case, model_kwargs=model_kwargs)
        if hasattr(path, '__call__'):
            path = path(actual)
        url = "/v1/actuals/%s%s" % (actual.pk, path)
        return api_client.delete(url)
    return inner


@pytest.fixture
def delete_test_case(api_client, establish_case):
    def inner(case):
        actual = establish_case(case)
        return api_client.delete("/v1/actuals/%s/" % actual.pk)
    return inner


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this actual.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {'status': 401}),
    ('another_public_case', {'status': 401}),
    (('logged_in', {'create': True}), {'status': 200}),
    (('multiple_budgets', {'login': True}), {
        'status': 403,
        'error': {
            'message': (
                "The user's subscription does not support multiple budgets."),
            'code': 'product_permission_error',
            'error_type': 'permission',
            'products': '__any__',
            'permission_id': 'multiple_budgets'
        }
    }),
    (('multiple_budgets', {'login': False}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    (('collaborator',
        {'login': True, 'access_type': Collaborator.ACCESS_TYPES.view_only}),
        {'status': 200}
    ),
    (('collaborator',
        {'login': True, 'access_type': Collaborator.ACCESS_TYPES.owner}),
        {'status': 200}
    ),
    (('collaborator',
        {'login': True, 'access_type': Collaborator.ACCESS_TYPES.editor}),
        {'status': 200}
    ),
    (('collaborator',
        {'login': False, 'access_type': Collaborator.ACCESS_TYPES.view_only}),
        {'status': 401}
    ),
    (('collaborator',
        {'login': False, 'access_type': Collaborator.ACCESS_TYPES.owner}),
        {'status': 401}
    ),
    (('collaborator',
        {'login': False, 'access_type': Collaborator.ACCESS_TYPES.editor}),
        {'status': 401}
    ),
])
def test_detail_read_permissions(case, assertions, detail_test_case,
        make_permission_assertions):
    response = detail_test_case(case)
    make_permission_assertions(response, case, assertions)


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this actual.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {'status': 401}),
    ('another_public_case', {'status': 401}),
    (('logged_in', {'create': True}), {'status': 204}),
    (('multiple_budgets', {'login': True}), {
        'status': 403,
        'error': {
            'message': (
                "The user's subscription does not support multiple budgets."),
            'code': 'product_permission_error',
            'error_type': 'permission',
            'products': '__any__',
            'permission_id': 'multiple_budgets'
        }
    }),
    (('multiple_budgets', {'login': False}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    (('collaborator',
        {'login': True, 'access_type': Collaborator.ACCESS_TYPES.view_only}),
        {'status': 403}
    ),
    (('collaborator',
        {'login': True, 'access_type': Collaborator.ACCESS_TYPES.owner}),
        {'status': 204}
    ),
    (('collaborator',
        {'login': True, 'access_type': Collaborator.ACCESS_TYPES.editor}),
        {'status': 204}
    ),
    (('collaborator',
        {'login': False, 'access_type': Collaborator.ACCESS_TYPES.view_only}),
        {'status': 401}
    ),
    (('collaborator',
        {'login': False, 'access_type': Collaborator.ACCESS_TYPES.owner}),
        {'status': 401}
    ),
    (('collaborator',
        {'login': False, 'access_type': Collaborator.ACCESS_TYPES.editor}),
        {'status': 401}
    ),
])
def test_delete_permissions(case, assertions, delete_test_case,
        make_permission_assertions):
    response = delete_test_case(case)
    make_permission_assertions(response, case, assertions)


@pytest.mark.parametrize('case,assertions', [
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    (('logged_in', {'create': True}), {'status': 200}),
    (('multiple_budgets', {'login': True}), {'status': 403}),
    (('multiple_budgets', {'login': False}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
])
def test_update_permissions(case, assertions, update_test_case,
        make_permission_assertions):
    response = update_test_case({'name': 'Test Actual'}, case)
    make_permission_assertions(response, case, assertions)


ACTUAL_DETAIL_ATTACHMENT_PERMISSIONS = [
    ('another_user', {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this actual.',
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {'status': 401}),
    ('another_public_case', {'status': 401}),
    (('multiple_budgets', {'login': True}), {
        'status': 403,
        'error': {
            'message': (
                "The user's subscription does not support multiple budgets."),
            'code': 'product_permission_error',
            'error_type': 'permission',
            'products': '__any__',
            'permission_id': 'multiple_budgets'
        }
    }),
    (('multiple_budgets', {'login': False}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    # Note: Currently, we do not allow uploading, deleting or updating of
    # attachments for entities that do not belong to the logged in user, even
    # when collaborating on the Budget.
    (('collaborator',
        {'login': True, 'access_type': Collaborator.ACCESS_TYPES.view_only}),
        {'status': 403}
    ),
    (('collaborator',
        {'login': True, 'access_type': Collaborator.ACCESS_TYPES.owner}),
        {'status': 403}
    ),
    (('collaborator',
        {'login': True, 'access_type': Collaborator.ACCESS_TYPES.editor}),
        {'status': 403}
    ),
    (('collaborator',
        {'login': False, 'access_type': Collaborator.ACCESS_TYPES.view_only}),
        {'status': 401}
    ),
    (('collaborator',
        {'login': False, 'access_type': Collaborator.ACCESS_TYPES.owner}),
        {'status': 401}
    ),
    (('collaborator',
        {'login': False, 'access_type': Collaborator.ACCESS_TYPES.editor}),
        {'status': 401}
    ),
]


@pytest.mark.parametrize(
    'case,assertions',
    ACTUAL_DETAIL_ATTACHMENT_PERMISSIONS + [
        (('logged_in', {'create': True}), {'status': 201})
    ]
)
def test_actual_detail_upload_attachment_permissions(case, assertions,
        detail_create_test_case, make_permission_assertions,
        test_uploaded_file):
    uploaded_file = test_uploaded_file('test.jpeg')
    response = detail_create_test_case(
        {'file': uploaded_file}, case, '/attachments/')
    make_permission_assertions(response, case, assertions, path='/attachments/')


@pytest.mark.parametrize(
    'case,assertions',
    ACTUAL_DETAIL_ATTACHMENT_PERMISSIONS + [
        (('logged_in', {'create': True}), {'status': 200}),
    ]
)
def test_actual_detail_read_attachment_permissions(case, assertions,
        detail_test_case, make_permission_assertions):
    response = detail_test_case(case, '/attachments/')
    make_permission_assertions(response, case, assertions, path='/attachments/')


@pytest.mark.parametrize(
    'case,assertions',
    ACTUAL_DETAIL_ATTACHMENT_PERMISSIONS + [
        (('logged_in', {'create': True}), {'status': 204}),
    ]
)
def test_actual_detail_delete_attachment_permissions(case, assertions,
        detail_delete_test_case, create_attachment, make_permission_assertions):
    def path(actual):
        return '/attachments/%s/' % actual.attachments.first().pk

    def model_kwargs(budget):
        # The attachments must belong to the same owner that the Actual will
        # have, and an Actual's ownership is dictated by the owner of the
        # related Budget.
        return {'attachments': [
            create_attachment(
                name='attachment1.jpeg',
                created_by=budget.user_owner
            ),
            create_attachment(
                name='attachment2.jpeg',
                created_by=budget.user_owner
            )
        ]}

    response = detail_delete_test_case(
        case,
        path,
        model_kwargs=model_kwargs
    )
    make_permission_assertions(response, case, assertions, path='/attachments/')
