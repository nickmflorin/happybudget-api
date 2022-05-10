# pylint: disable=redefined-outer-name
import pytest

from django.test import override_settings

from tests.permissions import ParameterizedCase


@pytest.fixture
def base_url():
    def inner(case, obj=None):
        if obj is None and case.method == 'GET':
            return "/v1/%ss/" % case.domain  # List response
        elif obj is None and case.method == 'POST':
            return "/v1/%ss/" % case.domain  # Create response
        return "/v1/budgets/"
    return inner


@pytest.fixture
def create_obj():
    def inner(budget, case):
        return budget
    return inner


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this budget.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase(
        'public_case',
        status=lambda case: 401 if case.path == '/actuals/' else 200
    ),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase('logged_in_staff', create=True, status=200),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase.collaborator(status=200),
])
@pytest.mark.parametrize('path', [
    '/', '/children/', '/actuals/', '/fringes/', '/markups/', '/groups/'])
@override_settings(STAFF_USER_GLOBAL_PERMISSIONS=True)
def test_budget_detail_read_permissions(case, path, detail_response):
    detail_response(case, domain="budget", path=path)


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this budget.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase('logged_in_staff', create=True, status=200),
    ParameterizedCase('multiple_budgets', login=True, status=200),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
@pytest.mark.parametrize('path', [
    '/', '/children/', '/fringes/', '/markups/', '/groups/'])
@override_settings(STAFF_USER_GLOBAL_PERMISSIONS=True)
def test_template_detail_read_permissions(case, path, detail_response):
    detail_response(case, domain="template", path=path)


@ParameterizedCase.parameterize([
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', status=200),
    ParameterizedCase('multiple_budgets', login=True, status=200),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
@pytest.mark.parametrize('domain', ['budget', 'template'])
def test_list_read_permissions(case, list_response, domain):
    list_response(case, domain=domain)


BUDGET_DELETE_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this budget.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=204),
    ParameterizedCase('multiple_budgets', login=True, status=204),
    ParameterizedCase.multiple_budgets_not_authenticated(),
]


@ParameterizedCase.parameterize(BUDGET_DELETE_PERMISSIONS + [
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase.collaborator(status=403)
])
def test_budget_delete_permissions(case, delete_response):
    delete_response(case, domain="budget")


@ParameterizedCase.parameterize(BUDGET_DELETE_PERMISSIONS)
def test_template_delete_permissions(case, delete_response):
    delete_response(case, domain="template")


BUDGET_CREATE_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this budget.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=201),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase.collaborator(view_only=403, status=201)
]


@ParameterizedCase.parameterize(BUDGET_CREATE_PERMISSIONS)
@pytest.mark.parametrize('path,data', [
    ('/children/', {}),
    ('/actuals/', {}),
    ('/fringes/', {})
])
def test_budget_detail_create_permissions(case, path, data,
        detail_create_response):
    detail_create_response(case, domain="budget", data=data, path=path)


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this budget.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    # This will still be a 403 because the User will have a Budget already.
    ParameterizedCase('logged_in', create=True, status=403, error={
        'message': (
            "The user's subscription does not support multiple budgets."),
        'code': 'product_permission_error',
        'error_type': 'permission',
        'products': '__any__',
        'permission_id': 'multiple_budgets'
    }),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase.collaborator(status=403)
])
def test_budget_duplicate_permissions(case, detail_create_response):
    detail_create_response(case, domain="budget", data={}, path="/duplicate/")


@pytest.mark.needtowrite
def test_budget_derive_permissions():
    pass


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this budget.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=201),
    ParameterizedCase('multiple_budgets', login=True, status=201),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
def test_template_duplicate_permissions(case, detail_create_response):
    detail_create_response(case, domain="template", data={}, path="/duplicate/")


@ParameterizedCase.parameterize(BUDGET_CREATE_PERMISSIONS)
def test_budget_detail_create_groups_permissions(case, f,
        detail_create_response):

    def post_data(budget):
        accounts = [f.create_budget_account(parent=budget)]
        return {'children': [a.pk for a in accounts], 'name': 'Test Group'}

    detail_create_response(
        case, domain="budget", data=post_data, path='/groups/')


@ParameterizedCase.parameterize(BUDGET_CREATE_PERMISSIONS)
def test_budget_detail_create_markups_permissions(case, f, models,
        detail_create_response):

    def post_data(budget):
        accounts = [f.create_budget_account(parent=budget)]
        return {
            'children': [a.pk for a in accounts],
            'identifier': '0001',
            'unit': models.Markup.UNITS.percent,
        }
    detail_create_response(
        case, domain="budget", data=post_data, path='/markups/')


TEMPLATE_CREATE_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this budget.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=201),
    ParameterizedCase('multiple_budgets', login=True, status=201),
    ParameterizedCase.multiple_budgets_not_authenticated(),
]


@ParameterizedCase.parameterize(TEMPLATE_CREATE_PERMISSIONS)
@pytest.mark.parametrize('path,data', [
    ('/children/', {}),
    ('/fringes/', {}),
])
def test_template_detail_create_permissions(case, path, data,
        detail_create_response):
    detail_create_response(case, domain="template", data=data, path=path)


@ParameterizedCase.parameterize(TEMPLATE_CREATE_PERMISSIONS)
def test_template_detail_create_groups_permissions(case, f,
        detail_create_response):

    def post_data(budget):
        accounts = [f.create_template_account(parent=budget)]
        return {'children': [a.pk for a in accounts], 'name': 'Test Group'}

    detail_create_response(
        case, domain="template", data=post_data, path='/groups/')


@ParameterizedCase.parameterize(TEMPLATE_CREATE_PERMISSIONS)
def test_template_detail_create_markups_permissions(case, f, models,
        detail_create_response):

    def post_data(budget):
        accounts = [f.create_template_account(parent=budget)]
        return {
            'children': [a.pk for a in accounts],
            'identifier': '0001',
            'unit': models.Markup.UNITS.percent,
        }

    detail_create_response(
        case, domain="template", data=post_data, path='/markups/')


@ParameterizedCase.parameterize([
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=False, status=201),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
def test_budget_create_permissions(case, create_response):
    create_response(case, domain="budget", data={'name': 'Test Budget'})


@ParameterizedCase.parameterize([
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=201),
    ParameterizedCase('multiple_budgets', login=True, status=201),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
def test_template_create_permissions(case, create_response):
    create_response(case, domain="template", data={'name': 'Test Budget'})


@ParameterizedCase.parameterize([
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    # Collaborators are not allowed to update the Budget itself, only the
    # owner of the Budget is allowed to do so.
    ParameterizedCase.collaborator(status=403)
])
def test_budget_update_permissions(case, update_response):
    update_response(case, domain="budget", data={'name': 'Test Budget'})


@ParameterizedCase.parameterize([
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase('multiple_budgets', login=True, status=200),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
def test_template_update_permissions(case, update_response):
    update_response(case, domain="template", data={'name': 'Test Budget'})


BUDGET_DETAIL_UPDATE_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this budget.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200)
]


@ParameterizedCase.parameterize(BUDGET_DETAIL_UPDATE_PERMISSIONS + [
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase.collaborator(view_only=403, status=200),
    ParameterizedCase('multiple_budgets', login=True, status=403),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
@pytest.mark.parametrize('path,data', [
    ('/bulk-update-children/', {'data': []}),
    ('/bulk-update-fringes/', {'data': []}),
    ('/bulk-update-actuals/', {'data': []}),
    ('/bulk-delete-children/', {'ids': []}),
    ('/bulk-delete-fringes/', {'ids': []}),
    ('/bulk-delete-actuals/', {'ids': []}),
    ('/bulk-create-children/', {'ids': []}),
    ('/bulk-create-fringes/', {'ids': []}),
    ('/bulk-create-actuals/', {'ids': []}),
])
def test_budget_bulk_permissions(case, detail_update_response, path, data):
    detail_update_response(case, domain="budget", path=path, data=data)


@ParameterizedCase.parameterize(BUDGET_DETAIL_UPDATE_PERMISSIONS + [
    ParameterizedCase('multiple_budgets', login=True, status=200),
])
@pytest.mark.parametrize('path,data', [
    ('/bulk-update-children/', {'data': []}),
    ('/bulk-update-fringes/', {'data': []}),
    ('/bulk-delete-children/', {'ids': []}),
    ('/bulk-delete-fringes/', {'ids': []}),
    ('/bulk-create-children/', {'ids': []}),
    ('/bulk-create-fringes/', {'ids': []}),
])
def test_template_bulk_permissions(case, detail_update_response, path, data):
    detail_update_response(case, domain="template", path=path, data=data)


@ParameterizedCase.parameterize([
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    # Collaborators are not allowed to import Budget actuals, only the
    # Collaborating owner is allowed to do so.  At least for the time being.
    ParameterizedCase.collaborator(view_only=403, editor=403, owner=200)
])
def test_bulk_import_actuals_permissions(case, detail_update_response, models,
        patch_plaid_transactions_response, mock_plaid_transactions,
        mock_plaid_accounts):
    patch_plaid_transactions_response(
        mock_plaid_transactions, mock_plaid_accounts)
    detail_update_response(
        case,
        domain="budget",
        path="/bulk-import-actuals/",
        data={
            "start_date": "2021-12-31",
            "public_token": "mock_public_token",
            "account_ids": ["test-id1", "test-id2"],
            "source": models.Actual.IMPORT_SOURCES.bank_account,
        }
    )
