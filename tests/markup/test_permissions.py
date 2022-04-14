# pylint: disable=redefined-outer-name
import pytest

from greenbudget.app.collaborator.models import Collaborator


@pytest.fixture
def another_user_case(api_client, user, create_user, create_budget,
        create_markup, create_account):
    def inner(domain, case_info=None):
        another_user = create_user()
        api_client.force_login(user)
        budget = create_budget(domain=domain, created_by=another_user)
        account = create_account(domain=domain, parent=budget)
        # Here, the user that created the Markup doesn't really matter, since
        # the ownership is dictated by the Budget.
        return create_markup(parent=budget, accounts=[account])
    return inner


@pytest.fixture
def public_case(api_client, user, create_budget, create_public_token,
        create_template, create_markup, create_account):
    def inner(domain, case_info=None):
        budget = create_budget(created_by=user)
        public_token = create_public_token(instance=budget)
        api_client.include_public_token(public_token)

        if domain == 'budget':
            account = create_account(domain=domain, parent=budget)
            return create_markup(parent=budget, accounts=[account])

        template = create_template(created_by=user)
        account = create_account(domain=domain, parent=template)
        return create_markup(parent=template, accounts=[account])
    return inner


@pytest.fixture
def logged_in_case(api_client, user, create_budget, create_markup,
        create_account):
    def inner(domain, case_info=None):
        api_client.force_login(user)
        if case_info and case_info.get('create', False) is True:
            budget = create_budget(domain=domain, created_by=user)
            account = create_account(domain=domain, parent=budget)
            return create_markup(parent=budget, accounts=[account])
        return None
    return inner


@pytest.fixture
def not_logged_in_case(user, create_budget, create_account, create_markup):
    def inner(domain, case_info=None):
        if case_info and case_info.get('create', False) is True:
            budget = create_budget(domain=domain, created_by=user)
            account = create_account(domain=domain, parent=budget)
            return create_markup(parent=budget, accounts=[account])
        return None
    return inner


@pytest.fixture
def multiple_case(api_client, create_budget, create_account, create_markup,
        user):
    def inner(domain, case_info=None):
        if case_info and case_info.get('login', True) is True:
            api_client.force_login(user)
        create_budget(domain=domain, created_by=user)
        budget = create_budget(domain=domain, created_by=user)
        account = create_account(domain=domain, parent=budget)
        return create_markup(parent=budget, accounts=[account])
    return inner


@pytest.fixture
def collaborator_case(api_client, user, create_user, create_budget,
        create_collaborator, create_account, create_markup):
    def inner(domain, case_info):
        collaborating_user = create_user()
        if case_info and case_info.get('login', True) is True:
            api_client.force_login(collaborating_user)

        budget = create_budget(created_by=user)
        create_collaborator(
            access_type=case_info['access_type'],
            user=collaborating_user,
            instance=budget
        )
        account = create_account(parent=budget)
        return create_markup(parent=budget, accounts=[account])
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
        markup = establish_case(domain, case)
        return api_client.patch("/v1/markups/%s/" % markup.pk, data=data)
    return inner


@pytest.fixture
def detail_test_case(api_client, establish_case):
    def inner(domain, case):
        markup = establish_case(domain, case)
        url = "/v1/markups/%s/" % markup.pk
        return api_client.get(url)
    return inner


@pytest.fixture
def delete_test_case(api_client, establish_case):
    def inner(domain, case):
        markup = establish_case(domain, case)
        return api_client.delete("/v1/markups/%s/" % markup.pk)
    return inner


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this markup.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    # Accessing the detail of a Markup via /markups/<pk>/ when in the public
    # domain is still not allowed.
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
def test_budget_markup_detail_read_permissions(case, assertions,
        detail_test_case, make_permission_assertions):
    response = detail_test_case("budget", case)
    make_permission_assertions(response, case, assertions)


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this markup.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {'status': 401}),
    (('logged_in', {'create': True}), {'status': 200}),
    (('multiple_budgets', {'login': True}), {'status': 200}),
    (('multiple_budgets', {'login': False}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }})
])
def test_template_markup_detail_read_permissions(case, assertions,
        detail_test_case, make_permission_assertions):
    response = detail_test_case("template", case)
    make_permission_assertions(response, case, assertions)


MARKUP_DELETE_PERMISSIONS = [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this markup.'),
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


@pytest.mark.parametrize('case,assertions', MARKUP_DELETE_PERMISSIONS + [
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
def test_budget_markup_delete_permissions(case, assertions, delete_test_case,
        make_permission_assertions):
    response = delete_test_case("budget", case)
    make_permission_assertions(response, case, assertions, path="/")


@pytest.mark.parametrize('case,assertions', MARKUP_DELETE_PERMISSIONS + [
    (('multiple_budgets', {'login': True}), {'status': 204})
])
def test_template_markup_delete_permissions(case, assertions, delete_test_case,
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
def test_budget_markup_update_permissions(case, assertions, update_test_case,
        make_permission_assertions):
    response = update_test_case("budget", {'description': 'Test Markup'}, case)
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
def test_template_markup_update_permissions(case, assertions, update_test_case,
        make_permission_assertions):
    response = update_test_case("template", {'description': 'Test Markup'}, case)
    make_permission_assertions(response, case, assertions, path="/")
