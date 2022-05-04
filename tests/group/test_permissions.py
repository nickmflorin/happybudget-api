# pylint: disable=redefined-outer-name
import pytest

from tests.permissions import ParameterizedCase


@pytest.fixture
def base_url():
    return "/v1/groups/"


@pytest.fixture
def create_obj(f):
    def inner(budget, case):
        model_kwargs = getattr(case, 'model_kwargs', {})
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(budget)
        return f.create_group(parent=budget, **model_kwargs)
    return inner


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this group.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=200),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase.collaborator(status=200),
])
def test_budget_group_detail_read_permissions(case, detail_response):
    detail_response(case, domain="budget")


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this group.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase('multiple_budgets', login=True, status=200),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
def test_template_group_detail_read_permissions(case, detail_response):
    detail_response(case, domain="template")


GROUP_DELETE_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this group.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=204),
    ParameterizedCase.multiple_budgets_not_authenticated(),
]


@ParameterizedCase.parameterize(GROUP_DELETE_PERMISSIONS + [
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase.collaborator(view_only=403, status=204),
])
def test_budget_group_delete_permissions(case, delete_response):
    delete_response(case, domain="budget")


@ParameterizedCase.parameterize(GROUP_DELETE_PERMISSIONS + [
    ParameterizedCase('multiple_budgets', login=True, status=204)
])
def test_template_group_delete_permissions(case, delete_response):
    delete_response(case, domain="template")


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this group.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase.collaborator(view_only=403, status=200),
])
def test_budget_group_update_permissions(case, update_response):
    update_response(case, domain="budget", data={"name": "Test Group"})


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this group.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase('multiple_budgets', login=True, status=200),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
def test_template_group_update_permissions(case, update_response):
    update_response(case, domain="template", data={"name": "Test Group"})
