# pylint: disable=redefined-outer-name
import pytest

from greenbudget.app.collaborator.models import Collaborator


@pytest.fixture
def another_user_case(api_client, user, f):
    def inner(domain, case_info=None):
        another_user = f.create_user()
        api_client.force_login(user)
        budget = f.create_budget(domain=domain, created_by=another_user)
        # Here, the user that created the Fringe doesn't really matter, since
        # the ownership is dictated by the Budget.
        return f.create_fringe(budget=budget)
    return inner


@pytest.fixture
def public_case(api_client, user, f):
    def inner(domain, case_info=None):
        budget = f.create_budget(created_by=user)
        public_token = f.create_public_token(instance=budget)
        api_client.include_public_token(public_token)
        if domain == 'budget':
            return f.create_fringe(budget=budget)
        template = f.create_template(created_by=user)
        return f.create_fringe(budget=template)
    return inner


@pytest.fixture
def logged_in_case(api_client, user, f):
    def inner(domain, case_info=None):
        fringe = None
        if case_info and case_info.get('create', False) is True:
            budget = f.create_budget(domain=domain, created_by=user)
            fringe = f.create_fringe(budget=budget)
        api_client.force_login(user)
        return fringe
    return inner


@pytest.fixture
def not_logged_in_case(user, f):
    def inner(domain, case_info=None):
        if case_info and case_info.get('create', False) is True:
            budget = f.create_budget(domain=domain, created_by=user)
            return f.create_fringe(budget=budget)
        return None
    return inner


@pytest.fixture
def multiple_case(api_client, f, user):
    def inner(domain, case_info=None):
        if case_info and case_info.get('login', True) is True:
            api_client.force_login(user)
        f.create_budget(domain=domain, created_by=user)
        budget = f.create_budget(domain=domain, created_by=user)
        return f.create_fringe(budget=budget)
    return inner


@pytest.fixture
def collaborator_case(api_client, user, f):
    def inner(domain, case_info):
        budget = f.create_budget(created_by=user)
        collaborating_user = f.create_user()
        if case_info and case_info.get('login', True) is True:
            api_client.force_login(collaborating_user)

        f.create_collaborator(
            access_type=case_info['access_type'],
            user=collaborating_user,
            instance=budget
        )
        return f.create_fringe(budget=budget)
    return inner


@pytest.fixture
def establish_case(another_user_case, multiple_case, collaborator_case,
        logged_in_case, not_logged_in_case, public_case):
    def inner(domain, case):
        cases = {
            'another_user': another_user_case,
            'not_logged_in': not_logged_in_case,
            'logged_in': logged_in_case,
            'multiple_budgets': multiple_case,
            'public_case': public_case,
            'collaborator': collaborator_case,
        }
        if isinstance(case, tuple):
            return cases[case[0]](domain, case[1])
        return cases[case](domain, {})
    return inner


@pytest.fixture
def update_test_case(api_client, establish_case):
    def inner(domain, data, case):
        fringe = establish_case(domain, case)
        return api_client.patch("/v1/fringes/%s/" % fringe.pk, data=data)
    return inner


@pytest.fixture
def detail_test_case(api_client, establish_case):
    def inner(domain, case):
        fringe = establish_case(domain, case)
        url = "/v1/fringes/%s/" % fringe.pk
        return api_client.get(url)
    return inner


@pytest.fixture
def delete_test_case(api_client, establish_case):
    def inner(domain, case):
        fringe = establish_case(domain, case)
        return api_client.delete("/v1/fringes/%s/" % fringe.pk)
    return inner


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this fringe.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    # Fringes are not publically accessible for any read, delete or update
    # operation.
    ('public_case', {'status': 401}),
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
def test_budget_fringe_detail_read_permissions(case, assertions,
        detail_test_case, make_permission_assertions):
    response = detail_test_case("budget", case)
    make_permission_assertions(response, case, assertions)


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this fringe.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    # Fringes are not publically accessible for any read, delete or update
    # operation.
    ('public_case', {'status': 401}),
    (('logged_in', {'create': True}), {'status': 200}),
    (('multiple_budgets', {'login': True}), {'status': 200}),
    (('multiple_budgets', {'login': False}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }})
])
def test_template_fringe_detail_read_permissions(case, assertions,
        detail_test_case, make_permission_assertions):
    response = detail_test_case("template", case)
    make_permission_assertions(response, case, assertions)


FRINGE_DELETE_PERMISSIONS = [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this fringe.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {'status': 401}),
    (('logged_in', {'create': True}), {'status': 204}),
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
]


@pytest.mark.parametrize('case,assertions', FRINGE_DELETE_PERMISSIONS + [
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
    })
])
def test_budget_fringe_delete_permissions(case, assertions, delete_test_case,
        make_permission_assertions):
    response = delete_test_case("budget", case)
    make_permission_assertions(response, case, assertions, path="/")


@pytest.mark.parametrize('case,assertions', FRINGE_DELETE_PERMISSIONS + [
    (('multiple_budgets', {'login': True}), {'status': 204})
])
def test_template_fringe_delete_permissions(case, assertions, delete_test_case,
        make_permission_assertions):
    response = delete_test_case("template", case)
    make_permission_assertions(response, case, assertions, path="/")


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
def test_budget_fringe_update_permissions(case, assertions, update_test_case,
        make_permission_assertions):
    response = update_test_case("budget", {'name': 'Test Fringe'}, case)
    make_permission_assertions(response, case, assertions, path="/")


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
    (('multiple_budgets', {'login': True}), {'status': 200}),
    (('multiple_budgets', {'login': False}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
])
def test_template_fringe_update_permissions(case, assertions, update_test_case,
        make_permission_assertions):
    response = update_test_case("template", {'name': 'Test Fringe'}, case)
    make_permission_assertions(response, case, assertions, path="/")
