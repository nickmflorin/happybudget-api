# pylint: disable=redefined-outer-name
import pytest

from tests.permissions import ParameterizedCase


@pytest.fixture
def base_url():
    return "/v1/markups/"


@pytest.fixture
def create_obj(f):
    def inner(budget, case):
        model_kwargs = getattr(case, 'model_kwargs', {})
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(budget)
        account = f.create_account(domain=case.domain, parent=budget)
        return f.create_markup(
            parent=budget,
            accounts=[account],
            **model_kwargs
        )
    return inner


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this markup.'),
        'code': 'permission_error',
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase.collaborator(status=200),
])
def test_budget_markup_detail_read_permissions(case, detail_response):
    detail_response(case, domain="budget")


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this markup.'),
        'code': 'permission_error',
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase('multiple_budgets', login=True, status=200),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
def test_template_markup_detail_read_permissions(case, detail_response):
    detail_response(case, domain="template")


MARKUP_DELETE_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this markup.'),
        'code': 'permission_error',
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=204),
    ParameterizedCase.multiple_budgets_not_authenticated(),
]


@ParameterizedCase.parameterize(MARKUP_DELETE_PERMISSIONS + [
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase.collaborator(view_only=403, status=204),
])
def test_budget_markup_delete_permissions(case, delete_response):
    delete_response(case, domain="budget")


@ParameterizedCase.parameterize(MARKUP_DELETE_PERMISSIONS + [
    ParameterizedCase('multiple_budgets', login=True, status=204)
])
def test_template_markup_delete_permissions(case, delete_response):
    delete_response(case, domain="template")


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this markup.'),
        'code': 'permission_error',
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase.collaborator(view_only=403, status=200),
])
def test_budget_markup_update_permissions(case, update_response):
    update_response(case, domain="budget", data={"name": "Test Markup"})


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this markup.'),
        'code': 'permission_error',
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase('multiple_budgets', login=True, status=200),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
def test_template_markup_update_permissions(case, update_response):
    update_response(case, domain="template", data={"name": "Test Markup"})
