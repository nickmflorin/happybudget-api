# pylint: disable=redefined-outer-name
import pytest

from tests.permissions import ParameterizedCase


@pytest.fixture
def base_url():
    return "/v1/subaccounts/"


@pytest.fixture
def create_obj(f):
    def inner(budget, case):
        # The domain of the Account & SubAccount should always be dictated by
        # the case domain.
        account = f.create_account(domain=case.domain, parent=budget)
        model_kwargs = getattr(case, 'model_kwargs', {})
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(account)
        # Here, the user that created the SubAccount doesn't really matter,
        # since the ownership is dictated by the Budget.
        return f.create_subaccount(
            domain=case.domain,
            parent=account,
            **model_kwargs
        )
    return inner


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this subaccount.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=200),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase.collaborator(status=200)
])
@pytest.mark.parametrize('path', ['/', '/children/', '/markups/', '/groups/'])
def test_budget_subaccount_detail_read_permissions(case, path, detail_response):
    detail_response(case, domain="budget", path=path)


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this subaccount.'),
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
def test_template_subaccount_detail_read_permissions(case, path,
        detail_response):
    detail_response(case, path=path, domain="template")


SUBACCOUNT_DELETE_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this subaccount.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=204),
    ParameterizedCase.multiple_budgets_not_authenticated(),
]


@ParameterizedCase.parameterize(SUBACCOUNT_DELETE_PERMISSIONS + [
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase.collaborator(view_only=403, owner=204, editor=204),
])
def test_budget_subaccount_delete_permissions(case, delete_response):
    delete_response(case, domain="budget")


@ParameterizedCase.parameterize(SUBACCOUNT_DELETE_PERMISSIONS + [
    ParameterizedCase('multiple_budgets', login=True, status=204)
])
def test_template_subaccount_delete_permissions(case, delete_response):
    delete_response(case, domain="template")


BUDGET_SUBACCOUNT_CREATE_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this subaccount.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=201),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase.collaborator(view_only=403, owner=201, editor=201),
]


@ParameterizedCase.parameterize(BUDGET_SUBACCOUNT_CREATE_PERMISSIONS)
@pytest.mark.parametrize('path,data', [('/children/', {})])
def test_budget_subaccount_detail_create_permissions(case, path, data,
        detail_create_response):
    detail_create_response(case, domain="budget", data=data, path=path)


@ParameterizedCase.parameterize(BUDGET_SUBACCOUNT_CREATE_PERMISSIONS)
def test_budget_subaccount_detail_create_groups_permissions(case, f,
        detail_create_response):

    def post_data(subaccount):
        accounts = [f.create_budget_subaccount(parent=subaccount)]
        return {'children': [a.pk for a in accounts], 'name': 'Test Group'}

    detail_create_response(
        case, domain="budget", data=post_data, path='/groups/')


@ParameterizedCase.parameterize(BUDGET_SUBACCOUNT_CREATE_PERMISSIONS)
def test_budget_subaccount_detail_create_markups_permissions(case, models, f,
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


TEMPLATE_SUBACCOUNT_CREATE_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this subaccount.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=201),
    ParameterizedCase('multiple_budgets', login=True, status=201),
    ParameterizedCase.multiple_budgets_not_authenticated(),
]


@ParameterizedCase.parameterize(TEMPLATE_SUBACCOUNT_CREATE_PERMISSIONS)
@pytest.mark.parametrize('path,data', [('/children/', {})])
def test_template_subaccount_detail_create_permissions(case, path, data,
        detail_create_response):
    detail_create_response(
        case, domain="template", data=data, path=path)


@ParameterizedCase.parameterize(TEMPLATE_SUBACCOUNT_CREATE_PERMISSIONS)
def test_template_subaccount_detail_create_groups_permissions(case, f,
        detail_create_response):

    def post_data(subaccount):
        accounts = [f.create_template_subaccount(parent=subaccount)]
        return {'children': [a.pk for a in accounts], 'name': 'Test Group'}

    detail_create_response(
        case, domain="template", data=post_data, path='/groups/')


@ParameterizedCase.parameterize(TEMPLATE_SUBACCOUNT_CREATE_PERMISSIONS)
def test_template_subaccount_detail_create_markups_permissions(case, models, f,
        detail_create_response):

    def post_data(account):
        subaccounts = [f.create_template_subaccount(parent=account)]
        return {
            'children': [a.pk for a in subaccounts],
            'identifier': '0001',
            'unit': models.Markup.UNITS.percent,
        }

    detail_create_response(
        case, domain="template", data=post_data, path='/markups/')


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this subaccount.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    ParameterizedCase.collaborator(view_only=403, owner=200, editor=200),
])
def test_budget_subaccount_update_permissions(case, update_response):
    update_response(case, domain="budget", data={'name': 'Test Sub Account'})


@ParameterizedCase.parameterize([
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this subaccount.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('logged_in', create=True, status=200),
    ParameterizedCase('multiple_budgets', login=True, status=200),
    ParameterizedCase.multiple_budgets_not_authenticated(),
])
def test_template_subaccount_update_permissions(case, update_response):
    update_response(case, domain="template", data={'name': 'Test Sub Account'})


SUBACCOUNT_DETAIL_ATTACHMENT_PERMISSIONS = [
    ParameterizedCase(name='another_user', status=403, error={
        'message': (
            'The user must does not have permission to view this subaccount.'),
        'code': 'permission_error',
        'error_type': 'permission'
    }),
    ParameterizedCase.not_logged_in(),
    ParameterizedCase('public_case', status=401),
    ParameterizedCase('another_public_case', status=401),
    ParameterizedCase.multiple_budgets_restricted(),
    ParameterizedCase.multiple_budgets_not_authenticated(),
    # Note: Currently, we do not allow uploading, deleting or updating of
    # attachments for entities that do not belong to the logged in user, even
    # when collaborating on the Budget.
    ParameterizedCase.collaborator(status=403)
]


@ParameterizedCase.parameterize(SUBACCOUNT_DETAIL_ATTACHMENT_PERMISSIONS + [
    ParameterizedCase('logged_in', create=True, status=201),
])
def test_subaccount_detail_upload_attachment_permissions(case,
        detail_create_response, test_uploaded_file):
    uploaded_file = test_uploaded_file('test.jpeg')
    detail_create_response(case,
        domain='budget', data={'file': uploaded_file}, path='/attachments/')


@ParameterizedCase.parameterize(SUBACCOUNT_DETAIL_ATTACHMENT_PERMISSIONS + [
    ParameterizedCase('logged_in', create=True, status=200),
])
def test_subaccount_detail_read_attachment_permissions(case, detail_response):
    detail_response(case, domain='budget', path='/attachments/')


@ParameterizedCase.parameterize(SUBACCOUNT_DETAIL_ATTACHMENT_PERMISSIONS + [
    ParameterizedCase('logged_in', create=True, status=204),
])
def test_subaccount_detail_delete_attachment_permissions(case, f,
        delete_response):
    def path(subaccount):
        return '/attachments/%s/' % subaccount.attachments.first().pk

    def model_kwargs(account):
        # The attachments must belong to the same owner that the SubAccount will
        # have, and an SubAccount's ownership is dictated by the owner of the
        # related Budget.
        return {'attachments': [
            f.create_attachment(
                name='attachment1.jpeg',
                created_by=account.user_owner
            ),
            f.create_attachment(
                name='attachment2.jpeg',
                created_by=account.user_owner
            )
        ]}

    delete_response(case, domain='budget', path=path, model_kwargs=model_kwargs)
