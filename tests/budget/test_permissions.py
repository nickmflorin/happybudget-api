# pylint: disable=redefined-outer-name
import pytest

from django.test import override_settings
from greenbudget.app.collaborator.models import Collaborator


@pytest.fixture
def another_user_case(api_client, user, create_user, create_budget):
    def inner(domain, case_info=None):
        another_user = create_user()
        api_client.force_login(user)
        return create_budget(domain=domain, created_by=another_user)
    return inner


@pytest.fixture
def staff_user_case(api_client, staff_user, user, create_budget):
    def inner(domain, case_info=None):
        api_client.force_login(staff_user)
        return create_budget(domain=domain, created_by=user)
    return inner


@pytest.fixture
def public_case(api_client, user, create_budget, create_public_token,
        create_template):
    def inner(domain, case_info=None):
        budget = create_budget(created_by=user)
        public_token = create_public_token(instance=budget)
        api_client.include_public_token(public_token)
        if domain == 'budget':
            return budget
        return create_template(created_by=user)
    return inner


@pytest.fixture
def another_public_case(api_client, user, create_budget, create_template,
        create_public_token):
    def inner(domain, case_info=None):
        budget = create_budget(created_by=user)
        another_budget = create_budget(created_by=user)
        public_token = create_public_token(instance=another_budget)
        api_client.include_public_token(public_token)
        if domain == 'budget':
            return budget
        return create_template(created_by=user)
    return inner


@pytest.fixture
def logged_in_case(api_client, user, create_budget):
    def inner(domain, case_info=None):
        budget = None
        if case_info and case_info.get('create', False) is True:
            budget = create_budget(domain=domain, created_by=user)
        api_client.force_login(user)
        return budget
    return inner


@pytest.fixture
def not_logged_in_case(user, create_budget):
    def inner(domain, case_info=None):
        if case_info and case_info.get('create', False) is True:
            return create_budget(domain=domain, created_by=user)
        return None
    return inner


@pytest.fixture
def multiple_case(api_client, create_budget, user):
    def inner(domain, case_info=None):
        create_budget(domain=domain, created_by=user)
        budget = create_budget(domain=domain, created_by=user)
        if case_info and case_info.get('login', True) is True:
            api_client.force_login(user)
        return budget
    return inner


@pytest.fixture
def collaborator_case(api_client, user, create_user, create_budget,
        create_collaborator):
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
        return budget
    return inner


@pytest.fixture
def establish_case(another_user_case, multiple_case, another_public_case,
        collaborator_case, logged_in_case, not_logged_in_case, staff_user_case,
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
            'staff_user': staff_user_case
        }
        if isinstance(case, tuple):
            return cases[case[0]](domain, case[1])
        return cases[case](domain, {})
    return inner


@pytest.fixture
def list_test_case(api_client, establish_case):
    def inner(domain, case):
        establish_case(domain, case)
        return api_client.get("/v1/%ss/" % domain)
    return inner


@pytest.fixture
def delete_test_case(api_client, establish_case):
    def inner(domain, case):
        budget = establish_case(domain, case)
        return api_client.delete("/v1/budgets/%s/" % budget.pk)
    return inner


@pytest.fixture
def create_test_case(api_client, establish_case):
    def inner(domain, data, case):
        establish_case(domain, case)
        return api_client.post("/v1/%ss/" % domain, data=data)
    return inner


@pytest.fixture
def update_test_case(api_client, establish_case):
    def inner(domain, data, case):
        budget = establish_case(domain, case)
        return api_client.patch("/v1/budgets/%s/" % budget.pk, data=data)
    return inner


@pytest.fixture
def detail_test_case(api_client, establish_case):
    def inner(domain, case, path="/"):
        budget = establish_case(domain, case)
        url = "/v1/budgets/%s%s" % (budget.pk, path)
        return api_client.get(url)
    return inner


@pytest.fixture
def detail_create_test_case(api_client, establish_case):
    def inner(domain, data, case, path="/"):
        budget = establish_case(domain, case)
        url = "/v1/budgets/%s%s" % (budget.pk, path)
        if hasattr(data, '__call__'):
            data = data(budget)
        return api_client.post(url, data=data)
    return inner


@pytest.fixture
def detail_update_test_case(api_client, establish_case):
    def inner(domain, data, case, path="/"):
        budget = establish_case(domain, case)
        url = "/v1/budgets/%s%s" % (budget.pk, path)
        return api_client.patch(url, data=data)
    return inner


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {
        'status': lambda path: 401 if path == '/actuals/' else 200
    }),
    ('another_public_case', {'status': 401}),
    (('logged_in', {'create': True}), {'status': 200}),
    (('staff_user', {'create': True}), {'status': 200}),
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
    '/', '/children/', '/actuals/', '/fringes/', '/markups/', '/groups/'])
@override_settings(STAFF_USER_GLOBAL_PERMISSIONS=True)
def test_budget_detail_read_permissions(case, path, assertions, detail_test_case,
        make_permission_assertions):
    response = detail_test_case("budget", case, path)
    make_permission_assertions(response, case, assertions, path)


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
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
    '/', '/children/', '/fringes/', '/markups/', '/groups/'])
def test_template_detail_read_permissions(case, path, assertions,
        detail_test_case, make_permission_assertions):
    response = detail_test_case("template", case, path)
    make_permission_assertions(response, case, assertions, path)


@pytest.mark.parametrize('case,assertions', [
    ('not_logged_in', {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {'status': 401}),
    ('logged_in', {'status': 200}),
    (('multiple_budgets', {'login': True}), {'status': 200}),
    (('multiple_budgets', {'login': False}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
])
@pytest.mark.parametrize('domain', ['budget', 'template'])
def test_list_read_permissions(case, assertions, list_test_case, domain,
        make_permission_assertions):
    response = list_test_case(domain, case)
    make_permission_assertions(response, case, assertions, path="/")


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
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
def test_budget_delete_permissions(case, assertions, delete_test_case,
        make_permission_assertions):
    response = delete_test_case("budget", case)
    make_permission_assertions(response, case, assertions, path="/")


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    (('not_logged_in', {'create': True}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    (('logged_in', {'create': True}), {'status': 204}),
])
def test_template_delete_permissions(case, assertions, delete_test_case,
        make_permission_assertions):
    response = delete_test_case("template", case)
    make_permission_assertions(response, case, assertions, path="/")


BUDGET_CREATE_PERMISSIONS = [
    ('another_user', {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
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


@pytest.mark.parametrize('case,assertions', BUDGET_CREATE_PERMISSIONS)
@pytest.mark.parametrize('path,data', [
    ('/children/', {}),
    ('/actuals/', {}),
    ('/fringes/', {})
])
def test_budget_detail_create_permissions(case, path, data, assertions,
        detail_create_test_case, make_permission_assertions):
    response = detail_create_test_case("budget", data, case, path)
    make_permission_assertions(response, case, assertions, path)


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
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
    (('logged_in', {'create': True}), {'status': 403}),
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
def test_budget_duplicate_permissions(case, assertions,
        detail_create_test_case, make_permission_assertions):
    response = detail_create_test_case("budget", {}, case, "/duplicate/")
    make_permission_assertions(response, case, assertions, path="/duplicate/")


@pytest.mark.needtowrite
def test_budget_derive_permissions():
    pass


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
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
])
def test_template_duplicate_permissions(case, assertions,
        detail_create_test_case, make_permission_assertions):
    response = detail_create_test_case("template", {}, case, "/duplicate/")
    make_permission_assertions(response, case, assertions, path="/duplicate/")


@pytest.mark.parametrize('case,assertions', BUDGET_CREATE_PERMISSIONS)
def test_budget_detail_create_groups_permissions(case, assertions,
        detail_create_test_case, make_permission_assertions,
        create_budget_account):

    def post_data(budget):
        accounts = [create_budget_account(parent=budget)]
        return {'children': [a.pk for a in accounts], 'name': 'Test Group'}

    response = detail_create_test_case("budget", post_data, case, '/groups/')
    make_permission_assertions(response, case, assertions, path="/groups/")


@pytest.mark.parametrize('case,assertions', BUDGET_CREATE_PERMISSIONS)
def test_budget_detail_create_markups_permissions(case, assertions,
        detail_create_test_case, make_permission_assertions, models,
        create_budget_account):

    def post_data(budget):
        accounts = [create_budget_account(parent=budget)]
        return {
            'children': [a.pk for a in accounts],
            'identifier': '0001',
            'unit': models.Markup.UNITS.percent,
        }
    response = detail_create_test_case("budget", post_data, case, '/markups/')
    make_permission_assertions(response, case, assertions, path="/markups/")


TEMPLATE_CREATE_PERMISSIONS = [
    ('another_user', {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
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
@pytest.mark.parametrize('path,data', [
    ('/children/', {}),
    ('/fringes/', {}),
])
def test_template_detail_create_permissions(case, path, data, assertions,
        detail_create_test_case, make_permission_assertions):
    response = detail_create_test_case("template", data, case, path)
    make_permission_assertions(response, case, assertions, path)


@pytest.mark.parametrize('case,assertions', TEMPLATE_CREATE_PERMISSIONS)
def test_template_detail_create_groups_permissions(case, assertions,
        detail_create_test_case, make_permission_assertions,
        create_template_account):

    def post_data(budget):
        accounts = [create_template_account(parent=budget)]
        return {'children': [a.pk for a in accounts], 'name': 'Test Group'}

    response = detail_create_test_case("template", post_data, case, '/groups/')
    make_permission_assertions(response, case, assertions, path="/groups/")


@pytest.mark.parametrize('case,assertions', TEMPLATE_CREATE_PERMISSIONS)
def test_template_detail_create_markups_permissions(case, assertions,
        detail_create_test_case, make_permission_assertions, models,
        create_template_account):

    def post_data(budget):
        accounts = [create_template_account(parent=budget)]
        return {
            'children': [a.pk for a in accounts],
            'identifier': '0001',
            'unit': models.Markup.UNITS.percent,
        }
    response = detail_create_test_case("template", post_data, case, '/markups/')
    make_permission_assertions(response, case, assertions, path="/markups/")


@pytest.mark.parametrize('case,assertions', [
    ('not_logged_in', {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    (('logged_in', {'create': False}), {'status': 201}),
    (('multiple_budgets', {'login': True}), {'status': 403}),
    (('multiple_budgets', {'login': False}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
])
def test_budget_create_permissions(case, assertions, make_permission_assertions,
        create_test_case):
    response = create_test_case("budget", {'name': 'Test Budget'}, case)
    make_permission_assertions(response, case, assertions, path="/")


@pytest.mark.parametrize('case,assertions', [
    ('not_logged_in', {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    (('logged_in', {'create': False}), {'status': 201}),
    (('multiple_budgets', {'login': True}), {'status': 201}),
    (('multiple_budgets', {'login': False}), {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
])
def test_template_create_permissions(case, assertions, create_test_case,
        make_permission_assertions):
    response = create_test_case("template", {'name': 'Test Budget'}, case)
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
def test_budget_update_permissions(case, assertions, make_permission_assertions,
        update_test_case):
    response = update_test_case("budget", {'name': 'Test Budget'}, case)
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
def test_template_update_permissions(case, assertions, update_test_case,
        make_permission_assertions):
    response = update_test_case("template", {'name': 'Test Budget'}, case)
    make_permission_assertions(response, case, assertions, path="/")
