# pylint: disable=redefined-outer-name
import pytest

from greenbudget.app.collaborator.models import Collaborator


@pytest.fixture
def another_user_case(api_client, user, create_user, create_domain_budget,
        create_account):
    def inner(domain, case_info=None):
        another_user = create_user()
        api_client.force_login(user)
        budget = create_domain_budget(domain=domain, created_by=another_user)
        account = create_account(
            domain=domain,
            parent=budget,
            created_by=another_user
        )
        return account
    return inner


@pytest.fixture
def public_case(api_client, user, create_budget, create_public_token,
        create_template, create_budget_account, create_template_account):
    def inner(domain, case_info=None):
        budget = create_budget(created_by=user)
        public_token = create_public_token(instance=budget)
        api_client.include_public_token(public_token)

        if domain == 'budget':
            return create_budget_account(parent=budget, created_by=user)

        template = create_template(created_by=user)
        return create_template_account(created_by=user, parent=template)
    return inner


@pytest.fixture
def another_public_case(api_client, user, create_budget, create_template,
        create_public_token, create_budget_account, create_template_account):
    def inner(domain, case_info=None):
        budget = create_budget(created_by=user)
        another_budget = create_budget(created_by=user)
        public_token = create_public_token(instance=another_budget)
        api_client.include_public_token(public_token)

        if domain == 'budget':
            return create_budget_account(parent=budget, created_by=user)

        template = create_template(created_by=user)
        return create_template_account(created_by=user, parent=template)
    return inner


@pytest.fixture
def logged_in_case(api_client, user, create_domain_budget, create_account):
    def inner(domain, case_info=None):
        account = None
        if case_info and case_info.get('create', False) is True:
            budget = create_domain_budget(domain=domain, created_by=user)
            account = create_account(
                domain=domain,
                parent=budget,
                created_by=user
            )
        api_client.force_login(user)
        return account
    return inner


@pytest.fixture
def not_logged_in_case(user, create_domain_budget, create_account):
    def inner(domain, case_info=None):
        if case_info and case_info.get('create', False) is True:
            budget = create_domain_budget(domain=domain, created_by=user)
            return create_account(
                domain=domain,
                parent=budget,
                created_by=user
            )
        return None
    return inner


@pytest.fixture
def multiple_case(api_client, create_domain_budget, create_account, user):
    def inner(domain, case_info=None):
        create_domain_budget(domain=domain, created_by=user)
        budget = create_domain_budget(domain=domain, created_by=user)
        account = create_account(domain=domain, parent=budget, created_by=user)
        if case_info and case_info.get('login', True) is True:
            api_client.force_login(user)
        return account
    return inner


@pytest.fixture
def collaborator_case(api_client, user, create_user, create_budget,
        create_collaborator, create_budget_account):
    def inner(domain, case_info):
        budget = create_budget(created_by=user)
        collaborating_user = create_user()
        create_collaborator(
            access_type=case_info['access_type'],
            user=collaborating_user,
            instance=budget
        )
        if case_info and case_info.get('login', True) is True:
            api_client.force_login(collaborating_user)
        return create_budget_account(parent=budget, created_by=user)
    return inner


@pytest.fixture
def establish_case(another_user_case, multiple_case, another_public_case,
        collaborator_case, logged_in_case, not_logged_in_case,
        public_case):
    def inner(domain, case):
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
            return cases[case[0]](domain, case[1])
        return cases[case](domain, {})
    return inner


@pytest.fixture
def create_test_case(api_client, establish_case):
    def inner(domain, data, case):
        establish_case(domain, case)
        return api_client.post("/v1/accounts/", data=data)
    return inner


@pytest.fixture
def update_test_case(api_client, establish_case):
    def inner(domain, data, case):
        account = establish_case(domain, case)
        return api_client.patch("/v1/accounts/%s/" % account.pk, data=data)
    return inner


@pytest.fixture
def detail_test_case(api_client, establish_case):
    def inner(domain, case, path="/"):
        account = establish_case(domain, case)
        url = "/v1/accounts/%s%s" % (account.pk, path)
        return api_client.get(url)
    return inner


@pytest.fixture
def delete_test_case(api_client, establish_case):
    def inner(domain, case):
        account = establish_case(domain, case)
        return api_client.delete("/v1/accounts/%s/" % account.pk)
    return inner


@pytest.fixture
def detail_create_test_case(api_client, establish_case):
    def inner(domain, data, case, path="/"):
        account = establish_case(domain, case)
        url = "/v1/accounts/%s%s" % (account.pk, path)
        if hasattr(data, '__call__'):
            data = data(account)
        return api_client.post(url, data=data)
    return inner


@pytest.fixture
def make_assertions():
    def evaluate(path, assertion):
        if hasattr(assertion, '__call__'):
            return assertion(path)
        return assertion

    def inner(response, case, path, assertions):
        if 'status' in assertions:
            status_code = evaluate(path, assertions['status'])
            assert response.status_code == status_code, \
                f"The expected status code for path {path}, case {case}, " \
                f"was {status_code}, but the response had status code " \
                f"{response.status_code}."
        if 'error' in assertions:
            error = status_code = evaluate(path, assertions['error'])
            assert response.json() == {'errors': [error]}
    return inner


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this account.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {'status': 200}),
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
@pytest.mark.parametrize('path', [
    '/', '/children/', '/markups/', '/groups/'])
def test_budget_account_detail_read_permissions(case, path, assertions,
        detail_test_case, make_assertions):
    response = detail_test_case("budget", case, path)
    make_assertions(response, case, path, assertions)


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this account.'),
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
    }}),
])
@pytest.mark.parametrize('path', [
    '/', '/children/', '/markups/', '/groups/'])
def test_template_account_detail_read_permissions(case, path, assertions,
        detail_test_case, make_assertions):
    response = detail_test_case("template", case, path)
    make_assertions(response, case, path, assertions)


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this account.'),
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
    (('multiple_budgets', {'login': True}), {'status': 204}),
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
])
@pytest.mark.parametrize('domain', ['budget', 'template'])
def test_delete_permissions(case, assertions, delete_test_case, domain,
        make_assertions):
    response = delete_test_case(domain, case)
    make_assertions(response, case, "/", assertions)


ACCOUNT_CREATE_PERMISSIONS = [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this account.'),
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
    (('logged_in', {'create': True}), {'status': 201}),
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
        {'status': 201}
    ),
    (('collaborator',
        {'login': True, 'access_type': Collaborator.ACCESS_TYPES.editor}),
        {'status': 201}
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


@pytest.mark.parametrize('case,assertions', ACCOUNT_CREATE_PERMISSIONS)
@pytest.mark.parametrize('path,data', [('/children/', {})])
def test_budget_account_detail_create_permissions(case, path, data, assertions,
        detail_create_test_case, make_assertions):
    response = detail_create_test_case("budget", data, case, path)
    make_assertions(response, case, path, assertions)


@pytest.mark.parametrize('case,assertions', ACCOUNT_CREATE_PERMISSIONS)
def test_budget_account_detail_create_groups_permissions(case, assertions,
        detail_create_test_case, make_assertions, create_budget_subaccount):

    def post_data(account):
        accounts = [create_budget_subaccount(parent=account)]
        return {'children': [a.pk for a in accounts], 'name': 'Test Group'}

    response = detail_create_test_case("budget", post_data, case, '/groups/')
    make_assertions(response, case, '/groups/', assertions)


@pytest.mark.needtowrite
def test_budget_account_detail_create_markups_permissions():
    pass


TEMPLATE_CREATE_PERMISSIONS = [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this account.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {'status': 401}),
    (('logged_in', {'create': True}), {'status': 201}),
    (('multiple_budgets', {'login': True}), {'status': 201}),
    (('multiple_budgets', {'login': False}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
]


@pytest.mark.parametrize('case,assertions', TEMPLATE_CREATE_PERMISSIONS)
@pytest.mark.parametrize('path,data', [('/children/', {})])
def test_template_account_detail_create_permissions(case, path, data, assertions,
        detail_create_test_case, make_assertions):
    response = detail_create_test_case("template", data, case, path)
    make_assertions(response, case, path, assertions)


@pytest.mark.parametrize('case,assertions', TEMPLATE_CREATE_PERMISSIONS)
def test_template_account_detail_create_groups_permissions(case, assertions,
        detail_create_test_case, make_assertions, create_template_subaccount):

    def post_data(account):
        accounts = [create_template_subaccount(parent=account)]
        return {'children': [a.pk for a in accounts], 'name': 'Test Group'}

    response = detail_create_test_case("template", post_data, case, '/groups/')
    make_assertions(response, case, '/groups/', assertions)


@pytest.mark.needtowrite
def test_template_account_detail_create_markups_permissions():
    pass


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
def test_budget_account_update_permissions(case, assertions, make_assertions,
        update_test_case):
    response = update_test_case("budget", {'name': 'Test Account'}, case)
    make_assertions(response, case, "/", assertions)


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
def test_template_account_update_permissions(case, assertions, make_assertions,
        update_test_case):
    response = update_test_case("template", {'name': 'Test Account'}, case)
    make_assertions(response, case, "/", assertions)
