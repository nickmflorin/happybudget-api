# pylint: disable=redefined-outer-name
import pytest

from tests.permissions import ParameterizedCase


@pytest.fixture
def base_url():
    return "/v1/actuals/"


@pytest.fixture
def create_obj(f):
    def inner(budget, case):
        model_kwargs = getattr(case, 'model_kwargs', {})
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(budget)
        return f.create_actual(budget=budget, **model_kwargs)
    return inner


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this actual.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    # Public domain does not yet include access to actuals.
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase.collaborator(status=200),
])
def test_detail_read_permissions(case, detail_response):
    detail_response(case)


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this actual.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=204),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase.collaborator(view_only=403, status=204),
])
def test_delete_permissions(case, delete_response):
    delete_response(case)


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this actual.'),
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
def test_update_permissions(case, update_response):
    update_response(case, data={'name': 'Test Actual'})


ACTUAL_DETAIL_ATTACHMENT_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this actual.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase.multiple_budgets_restricted(),
    # Note: Currently, we do not allow uploading, deleting or updating of
    # attachments for entities that do not belong to the logged in user, even
    # when collaborating on the Budget.
    ParameterizedCase.collaborator(status=403),
]


@ParameterizedCase.parameterize(ACTUAL_DETAIL_ATTACHMENT_PERMISSIONS + [
    ParameterizedCase('logged_in', create=True, status=201),
])
def test_actual_detail_upload_attachment_permissions(case, test_uploaded_file,
        detail_create_response):
    uploaded_file = test_uploaded_file('test.jpeg')
    detail_create_response(
        case, data={'file': uploaded_file}, path='/attachments/')


@ParameterizedCase.parameterize(ACTUAL_DETAIL_ATTACHMENT_PERMISSIONS + [
    ParameterizedCase('logged_in', create=True, status=200),
])
def test_actual_detail_read_attachment_permissions(case, detail_response):
    detail_response(case, path='/attachments/')


@ParameterizedCase.parameterize(ACTUAL_DETAIL_ATTACHMENT_PERMISSIONS + [
    ParameterizedCase('logged_in', create=True, status=204),
])
def test_actual_detail_delete_attachment_permissions(case, f, delete_response):
    def path(actual):
        return '/attachments/%s/' % actual.attachments.first().pk

    def model_kwargs(budget):
        # The attachments must belong to the same owner that the SubAccount will
        # have, and an SubAccount's ownership is dictated by the owner of the
        # related Budget.
        return {'attachments': [
            f.create_attachment(
                name='attachment1.jpeg',
                created_by=budget.user_owner
            ),
            f.create_attachment(
                name='attachment2.jpeg',
                created_by=budget.user_owner
            )
        ]}

    delete_response(case, path=path, model_kwargs=model_kwargs)
