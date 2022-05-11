# pylint: disable=redefined-outer-name
import pytest

from happybudget.app.collaborator.models import Collaborator
from tests.permissions import ParameterizedCase


@pytest.fixture
def base_url():
    return "/v1/accounts/"


@pytest.fixture
def create_obj(f):
    def inner(budget, case):
        # The domain of the Account should always be dictated by the case domain.
        return f.create_account(domain=case.domain, parent=budget)
    return inner


@pytest.mark.parametrize('case', [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this account.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=200),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase(
        'collaborator',
        login=True,
        access_type=Collaborator.ACCESS_TYPES.view_only,
        status=200
    ),
    ParameterizedCase(
        'collaborator',
        login=True,
        access_type=Collaborator.ACCESS_TYPES.owner,
        status=200
    ),
    ParameterizedCase(
        'collaborator',
        login=True,
        access_type=Collaborator.ACCESS_TYPES.editor,
        status=200
    ),
    ParameterizedCase(
        'collaborator',
        login=False,
        access_type=Collaborator.ACCESS_TYPES.view_only,
        status=401
    ),
    ParameterizedCase(
        'collaborator',
        login=False,
        access_type=Collaborator.ACCESS_TYPES.owner,
        status=401
    ),
    ParameterizedCase(
        'collaborator',
        login=False,
        access_type=Collaborator.ACCESS_TYPES.editor,
        status=401
    )
])
@pytest.mark.parametrize('path', ['/', '/children/', '/markups/', '/groups/'])
def test_budget_account_detail_read_permissions(case, path, detail_response):
    detail_response(case, path=path, domain="budget")


@pytest.mark.parametrize('case', [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this account.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase('multiple_budgets', login=True, status=200),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
@pytest.mark.parametrize('path', ['/', '/children/', '/markups/', '/groups/'])
def test_template_account_detail_read_permissions(case, path, detail_response):
    detail_response(case, path=path, domain="template")


ACCOUNT_DELETE_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this account.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=204),
    ParameterizedCase.multiple_budgets_not_authenticated(),
]


@pytest.mark.parametrize('case', ACCOUNT_DELETE_PERMISSIONS + [
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase(
        'collaborator',
        login=True,
        access_type=Collaborator.ACCESS_TYPES.view_only,
        status=403
    ),
    ParameterizedCase(
        'collaborator',
        login=True,
        access_type=Collaborator.ACCESS_TYPES.owner,
        status=204
    ),
    ParameterizedCase(
        'collaborator',
        login=True,
        access_type=Collaborator.ACCESS_TYPES.editor,
        status=204
    ),
    ParameterizedCase(
        'collaborator',
        login=False,
        access_type=Collaborator.ACCESS_TYPES.view_only,
        status=401
    ),
    ParameterizedCase(
        'collaborator',
        login=False,
        access_type=Collaborator.ACCESS_TYPES.owner,
        status=401
    ),
    ParameterizedCase(
        'collaborator',
        login=False,
        access_type=Collaborator.ACCESS_TYPES.editor,
        status=401
    )
])
def test_budget_account_delete_permissions(case, delete_response):
    delete_response(case, domain="budget")


@pytest.mark.parametrize('case', ACCOUNT_DELETE_PERMISSIONS + [
    ParameterizedCase('multiple_budgets', login=True, status=204)
])
def test_template_account_delete_permissions(case, delete_response):
    delete_response(case, domain="template")


BUDGET_ACCOUNT_CREATE_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this account.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=201),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase(
        'collaborator',
        login=True,
        access_type=Collaborator.ACCESS_TYPES.view_only,
        status=403
    ),
    ParameterizedCase(
        'collaborator',
        login=True,
        access_type=Collaborator.ACCESS_TYPES.owner,
        status=201
    ),
    ParameterizedCase(
        'collaborator',
        login=True,
        access_type=Collaborator.ACCESS_TYPES.editor,
        status=201
    ),
    ParameterizedCase(
        'collaborator',
        login=False,
        access_type=Collaborator.ACCESS_TYPES.view_only,
        status=401
    ),
    ParameterizedCase(
        'collaborator',
        login=False,
        access_type=Collaborator.ACCESS_TYPES.owner,
        status=401
    ),
    ParameterizedCase(
        'collaborator',
        login=False,
        access_type=Collaborator.ACCESS_TYPES.editor,
        status=401
    )
]


@pytest.mark.parametrize('case', BUDGET_ACCOUNT_CREATE_PERMISSIONS)
@pytest.mark.parametrize('path,data', [('/children/', {})])
def test_budget_account_detail_create_permissions(case, path, data,
        detail_create_response):
    detail_create_response(case, data=data, path=path, domain="budget")


@pytest.mark.parametrize('case', BUDGET_ACCOUNT_CREATE_PERMISSIONS)
def test_budget_account_detail_create_groups_permissions(case, f,
        detail_create_response):

    def post_data(account):
        subaccounts = [f.create_budget_subaccount(parent=account)]
        return {'children': [a.pk for a in subaccounts], 'name': 'Test Group'}

    detail_create_response(
        case, domain="budget", data=post_data, path='/groups/')


@pytest.mark.parametrize('case', BUDGET_ACCOUNT_CREATE_PERMISSIONS)
def test_budget_account_detail_create_markups_permissions(case, models, f,
        detail_create_response):

    def post_data(account):
        subaccounts = [f.create_budget_subaccount(parent=account)]
        return {
            'children': [a.pk for a in subaccounts],
            'identifier': '0001',
            'unit': models.Markup.UNITS.percent,
        }

    detail_create_response(
        case, domain="budget", data=post_data, path='/markups/')


TEMPLATE_ACCOUNT_CREATE_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this account.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=201),
    ParameterizedCase('multiple_budgets', login=True, status=201),
    ParameterizedCase.multiple_budgets_not_authenticated(),
]


@pytest.mark.parametrize('case', TEMPLATE_ACCOUNT_CREATE_PERMISSIONS)
@pytest.mark.parametrize('path,data', [('/children/', {})])
def test_template_account_detail_create_permissions(case, path, data,
        detail_create_response):
    detail_create_response(case, domain="template", data=data, path=path)


@pytest.mark.parametrize('case', TEMPLATE_ACCOUNT_CREATE_PERMISSIONS)
def test_template_account_detail_create_groups_permissions(case, f,
        detail_create_response, make_permission_assertions):

    def post_data(account):
        subaccounts = [f.create_template_subaccount(parent=account)]
        return {'children': [a.pk for a in subaccounts], 'name': 'Test Group'}

    detail_create_response(
        case, domain="template", data=post_data, path='/groups/')


@pytest.mark.parametrize('case', TEMPLATE_ACCOUNT_CREATE_PERMISSIONS)
def test_template_account_detail_create_markups_permissions(case, models, f,
        detail_create_response, make_permission_assertions):

    def post_data(account):
        subaccounts = [f.create_template_subaccount(parent=account)]
        return {
            'children': [a.pk for a in subaccounts],
            'identifier': '0001',
            'unit': models.Markup.UNITS.percent,
        }

    detail_create_response(
        case, domain="template", data=post_data, path='/markups/')


@pytest.mark.parametrize('case', [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this account.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase(
        'collaborator',
        login=True,
        access_type=Collaborator.ACCESS_TYPES.view_only,
        status=403
    ),
    ParameterizedCase(
        'collaborator',
        login=True,
        access_type=Collaborator.ACCESS_TYPES.owner,
        status=200
    ),
    ParameterizedCase(
        'collaborator',
        login=True,
        access_type=Collaborator.ACCESS_TYPES.editor,
        status=200
    ),
    ParameterizedCase(
        'collaborator',
        login=False,
        access_type=Collaborator.ACCESS_TYPES.view_only,
        status=401
    ),
    ParameterizedCase(
        'collaborator',
        login=False,
        access_type=Collaborator.ACCESS_TYPES.owner,
        status=401
    ),
    ParameterizedCase(
        'collaborator',
        login=False,
        access_type=Collaborator.ACCESS_TYPES.editor,
        status=401
    )
])
def test_budget_account_update_permissions(case, update_response):
    update_response(case, domain="budget", data={"name": "Test Account"})


@pytest.mark.parametrize('case', [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this account.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase('multiple_budgets', login=True, status=200),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
def test_template_account_update_permissions(case, update_response):
    update_response(case, domain="template", data={"name": "Test Account"})
