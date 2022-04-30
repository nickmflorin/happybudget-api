# pylint: disable=redefined-outer-name
import pytest

from greenbudget.app.collaborator.models import Collaborator


@pytest.fixture
def another_user_case(api_client, user, create_user, create_budget,
        create_account, create_subaccount):
    def inner(domain, case_info=None, model_kwargs=None):
        another_user = create_user()
        api_client.force_login(user)
        budget = create_budget(domain=domain, created_by=another_user)
        account = create_account(domain=domain, parent=budget)

        model_kwargs = model_kwargs or {}
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(account)

        # Here, the user that created the SubAccount doesn't really matter,
        # since the ownership is dictated by the Budget.
        return create_subaccount(domain=domain, parent=account, **model_kwargs)
    return inner


@pytest.fixture
def public_case(api_client, user, create_budget, create_public_token,
        create_template, create_budget_account, create_template_account,
        create_budget_subaccount, create_template_subaccount):
    def inner(domain, case_info=None, model_kwargs=None):
        budget = create_budget(created_by=user)
        public_token = create_public_token(instance=budget)
        api_client.include_public_token(public_token)

        model_kwargs = model_kwargs or {}

        if domain == 'budget':
            account = create_budget_account(parent=budget)
            if hasattr(model_kwargs, '__call__'):
                model_kwargs = model_kwargs(account)
            return create_budget_subaccount(parent=account, **model_kwargs)

        template = create_template(created_by=user)
        account = create_template_account(parent=template)
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(account)
        return create_template_subaccount(parent=account, **model_kwargs)
    return inner


@pytest.fixture
def another_public_case(api_client, user, create_budget, create_template,
        create_public_token, create_budget_account, create_template_account,
        create_budget_subaccount, create_template_subaccount):
    def inner(domain, case_info=None, model_kwargs=None):
        budget = create_budget(created_by=user)
        another_budget = create_budget(created_by=user)
        public_token = create_public_token(instance=another_budget)
        api_client.include_public_token(public_token)

        model_kwargs = model_kwargs or {}

        if domain == 'budget':
            account = create_budget_account(parent=budget)
            if hasattr(model_kwargs, '__call__'):
                model_kwargs = model_kwargs(account)
            return create_budget_subaccount(parent=account, **model_kwargs)

        template = create_template(created_by=user)
        account = create_template_account(parent=template)
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(account)
        return create_template_subaccount(parent=account, **model_kwargs)
    return inner


@pytest.fixture
def logged_in_case(api_client, user, create_budget, create_account,
        create_subaccount):
    def inner(domain, case_info=None, model_kwargs=None):
        api_client.force_login(user)
        if case_info and case_info.get('create', False) is True:
            budget = create_budget(domain=domain, created_by=user)
            account = create_account(domain=domain, parent=budget)
            model_kwargs = model_kwargs or {}
            if hasattr(model_kwargs, '__call__'):
                model_kwargs = model_kwargs(account)
            return create_subaccount(
                domain=domain,
                parent=account,
                **model_kwargs
            )
        return None
    return inner


@pytest.fixture
def not_logged_in_case(user, create_budget, create_account,
        create_subaccount):
    def inner(domain, case_info=None, model_kwargs=None):
        if case_info and case_info.get('create', False) is True:
            budget = create_budget(domain=domain, created_by=user)
            account = create_account(domain=domain, parent=budget)
            model_kwargs = model_kwargs or {}
            if hasattr(model_kwargs, '__call__'):
                model_kwargs = model_kwargs(account)
            return create_subaccount(
                domain=domain, parent=account, **model_kwargs)
        return None
    return inner


@pytest.fixture
def multiple_case(api_client, create_budget, create_account, user,
        create_subaccount):
    def inner(domain, case_info=None, model_kwargs=None):
        if case_info and case_info.get('login', True) is True:
            api_client.force_login(user)
        create_budget(domain=domain, created_by=user)
        budget = create_budget(domain=domain, created_by=user)
        account = create_account(domain=domain, parent=budget)
        model_kwargs = model_kwargs or {}
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(account)
        return create_subaccount(
            domain=domain,
            parent=account,
            **model_kwargs
        )
    return inner


@pytest.fixture
def collaborator_case(api_client, user, create_user, create_budget,
        create_collaborator, create_budget_account, create_budget_subaccount):
    def inner(domain, case_info, model_kwargs=None):
        budget = create_budget(created_by=user)
        collaborating_user = create_user()
        create_collaborator(
            access_type=case_info['access_type'],
            user=collaborating_user,
            instance=budget
        )
        if case_info and case_info.get('login', True) is True:
            api_client.force_login(collaborating_user)
        account = create_budget_account(parent=budget)
        model_kwargs = model_kwargs or {}
        if hasattr(model_kwargs, '__call__'):
            model_kwargs = model_kwargs(account)
        return create_budget_subaccount(parent=account, **model_kwargs)
    return inner


@pytest.fixture
def establish_case(another_user_case, multiple_case, another_public_case,
        collaborator_case, logged_in_case, not_logged_in_case, public_case):
    def inner(domain, case, model_kwargs=None):
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
            return cases[case[0]](
                domain=domain,
                case_info=case[1],
                model_kwargs=model_kwargs
            )
        return cases[case](
            domain=domain,
            case_info={},
            model_kwargs=model_kwargs
        )
    return inner


@pytest.fixture
def create_test_case(api_client, establish_case):
    def inner(domain, data, case):
        establish_case(domain, case)
        return api_client.post("/v1/subaccounts/", data=data)
    return inner


@pytest.fixture
def update_test_case(api_client, establish_case):
    def inner(domain, data, case):
        subaccount = establish_case(domain, case)
        return api_client.patch(
            "/v1/subaccounts/%s/" % subaccount.pk, data=data)
    return inner


@pytest.fixture
def detail_test_case(api_client, establish_case):
    def inner(domain, case, path="/"):
        subaccount = establish_case(domain, case)
        url = "/v1/subaccounts/%s%s" % (subaccount.pk, path)
        return api_client.get(url)
    return inner


@pytest.fixture
def delete_test_case(api_client, establish_case):
    def inner(domain, case):
        subaccount = establish_case(domain, case)
        return api_client.delete("/v1/subaccounts/%s/" % subaccount.pk)
    return inner


@pytest.fixture
def detail_delete_test_case(api_client, establish_case):
    def inner(domain, case, path="/", model_kwargs=None):
        subaccount = establish_case(domain, case, model_kwargs=model_kwargs)
        if hasattr(path, '__call__'):
            path = path(subaccount)
        url = "/v1/subaccounts/%s%s" % (subaccount.pk, path)
        return api_client.delete(url)
    return inner


@pytest.fixture
def detail_create_test_case(api_client, establish_case):
    def inner(domain, data, case, path="/"):
        subaccount = establish_case(domain, case)
        url = "/v1/subaccounts/%s%s" % (subaccount.pk, path)
        if hasattr(data, '__call__'):
            data = data(subaccount)
        return api_client.post(url, data=data)
    return inner


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this subaccount.'),
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
def test_budget_subaccount_detail_read_permissions(case, path, assertions,
        detail_test_case, make_permission_assertions):
    response = detail_test_case("budget", case, path)
    make_permission_assertions(response, case, assertions, path)


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this subaccount.'),
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
def test_template_subaccount_detail_read_permissions(case, path, assertions,
        detail_test_case, make_permission_assertions):
    response = detail_test_case("template", case, path)
    make_permission_assertions(response, case, assertions, path)


SUBACCOUNT_DELETE_PERMISSIONS = [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this subaccount.'),
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


@pytest.mark.parametrize('case,assertions', SUBACCOUNT_DELETE_PERMISSIONS + [
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
def test_budget_subaccount_delete_permissions(case, assertions, delete_test_case,
        make_permission_assertions):
    response = delete_test_case("budget", case)
    make_permission_assertions(response, case, assertions, path="/")


@pytest.mark.parametrize('case,assertions', SUBACCOUNT_DELETE_PERMISSIONS + [
    (('multiple_budgets', {'login': True}), {'status': 204})
])
def test_template_subaccount_delete_permissions(case, assertions,
        delete_test_case, make_permission_assertions):
    response = delete_test_case("template", case)
    make_permission_assertions(response, case, assertions, path="/")


BUDGET_SUBACCOUNT_CREATE_PERMISSIONS = [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this subaccount.'),
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


@pytest.mark.parametrize(
    'case,assertions', BUDGET_SUBACCOUNT_CREATE_PERMISSIONS)
@pytest.mark.parametrize('path,data', [('/children/', {})])
def test_budget_subaccount_detail_create_permissions(case, path, data,
        assertions, detail_create_test_case, make_permission_assertions):
    response = detail_create_test_case("budget", data, case, path)
    make_permission_assertions(response, case, assertions, path)


@pytest.mark.parametrize(
    'case,assertions', BUDGET_SUBACCOUNT_CREATE_PERMISSIONS)
def test_budget_subaccount_detail_create_groups_permissions(case, assertions,
        detail_create_test_case, make_permission_assertions,
        create_budget_subaccount):

    def post_data(subaccount):
        accounts = [create_budget_subaccount(parent=subaccount)]
        return {'children': [a.pk for a in accounts], 'name': 'Test Group'}

    response = detail_create_test_case("budget", post_data, case, '/groups/')
    make_permission_assertions(response, case, assertions, path='/groups/')


@pytest.mark.parametrize('case,assertions', BUDGET_SUBACCOUNT_CREATE_PERMISSIONS)
def test_budget_subaccount_detail_create_markups_permissions(case, assertions,
        detail_create_test_case, make_permission_assertions, models,
        create_budget_subaccount):

    def post_data(account):
        subaccounts = [create_budget_subaccount(parent=account)]
        return {
            'children': [a.pk for a in subaccounts],
            'identifier': '0001',
            'unit': models.Markup.UNITS.percent,
        }

    response = detail_create_test_case("budget", post_data, case, '/markups/')
    make_permission_assertions(response, case, assertions, path="/markups/")


TEMPLATE_SUBACCOUNT_CREATE_PERMISSIONS = [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this subaccount.'),
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


@pytest.mark.parametrize(
    'case,assertions', TEMPLATE_SUBACCOUNT_CREATE_PERMISSIONS)
@pytest.mark.parametrize('path,data', [('/children/', {})])
def test_template_subaccount_detail_create_permissions(case, path, data,
        assertions, detail_create_test_case, make_permission_assertions):
    response = detail_create_test_case("template", data, case, path)
    make_permission_assertions(response, case, assertions, path)


@pytest.mark.parametrize(
    'case,assertions', TEMPLATE_SUBACCOUNT_CREATE_PERMISSIONS)
def test_template_subaccount_detail_create_groups_permissions(case, assertions,
        detail_create_test_case, make_permission_assertions,
        create_template_subaccount):

    def post_data(subaccount):
        accounts = [create_template_subaccount(parent=subaccount)]
        return {'children': [a.pk for a in accounts], 'name': 'Test Group'}

    response = detail_create_test_case("template", post_data, case, '/groups/')
    make_permission_assertions(response, case, assertions, path='/groups/')


@pytest.mark.parametrize(
    'case,assertions', TEMPLATE_SUBACCOUNT_CREATE_PERMISSIONS)
def test_template_subaccount_detail_create_markups_permissions(case, assertions,
        detail_create_test_case, make_permission_assertions, models,
        create_template_subaccount):

    def post_data(account):
        subaccounts = [create_template_subaccount(parent=account)]
        return {
            'children': [a.pk for a in subaccounts],
            'identifier': '0001',
            'unit': models.Markup.UNITS.percent,
        }

    response = detail_create_test_case("template", post_data, case, '/markups/')
    make_permission_assertions(response, case, assertions, path="/markups/")


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
def test_budget_subaccount_update_permissions(case, assertions, update_test_case,
        make_permission_assertions):
    response = update_test_case("budget", {'name': 'Test Sub Account'}, case)
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
def test_template_subaccount_update_permissions(case, assertions,
        make_permission_assertions, update_test_case):
    response = update_test_case("template", {'name': 'Test Sub Account'}, case)
    make_permission_assertions(response, case, assertions, path="/")


SUBACCOUNT_DETAIL_ATTACHMENT_PERMISSIONS = [
    ('another_user', {'status': 403, 'error': {
        'message': (
            'The user must does not have permission to view this subaccount.'
        ),
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
    # Note: Currently, we do not allow uploading, deleting or updating of
    # attachments for entities that do not belong to the logged in user, even
    # when collaborating on the Budget.
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
]


@pytest.mark.parametrize(
    'case,assertions',
    SUBACCOUNT_DETAIL_ATTACHMENT_PERMISSIONS + [
        (('logged_in', {'create': True}), {'status': 201})
    ]
)
def test_subaccount_detail_upload_attachment_permissions(case, assertions,
        detail_create_test_case, make_permission_assertions,
        test_uploaded_file):
    uploaded_file = test_uploaded_file('test.jpeg')
    response = detail_create_test_case(
        "budget", {'file': uploaded_file}, case, '/attachments/')
    make_permission_assertions(response, case, assertions, path='/attachments/')


@pytest.mark.parametrize(
    'case,assertions',
    SUBACCOUNT_DETAIL_ATTACHMENT_PERMISSIONS + [
        (('logged_in', {'create': True}), {'status': 200}),
    ]
)
def test_subaccount_detail_read_attachment_permissions(case, assertions,
        detail_test_case, make_permission_assertions):
    response = detail_test_case("budget", case, '/attachments/')
    make_permission_assertions(response, case, assertions, path='/attachments/')


@pytest.mark.parametrize(
    'case,assertions',
    SUBACCOUNT_DETAIL_ATTACHMENT_PERMISSIONS + [
        (('logged_in', {'create': True}), {'status': 204}),
    ]
)
def test_subaccount_detail_delete_attachment_permissions(case, assertions,
        detail_delete_test_case, create_attachment, make_permission_assertions):
    def path(subaccount):
        return '/attachments/%s/' % subaccount.attachments.first().pk

    def model_kwargs(account):
        # The attachments must belong to the same owner that the SubAccount will
        # have, and an SubAccount's ownership is dictated by the owner of the
        # related Budget.
        return {'attachments': [
            create_attachment(
                name='attachment1.jpeg',
                created_by=account.user_owner
            ),
            create_attachment(
                name='attachment2.jpeg',
                created_by=account.user_owner
            )
        ]}

    response = detail_delete_test_case(
        "budget",
        case,
        path,
        model_kwargs=model_kwargs
    )
    make_permission_assertions(response, case, assertions, path='/attachments/')
