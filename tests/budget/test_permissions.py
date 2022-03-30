# pylint: disable=redefined-outer-name
import pytest

from greenbudget.app.collaborator.models import Collaborator


@pytest.fixture
def another_user_case(api_client, user, create_user, create_domain_budget):
    def inner(domain):
        another_user = create_user()
        api_client.force_login(user)
        return create_domain_budget(domain=domain, created_by=another_user)
    return inner


@pytest.fixture
def budget_public_case(api_client, user, create_budget, create_public_token):
    def inner():
        budget = create_budget(created_by=user)
        public_token = create_public_token(instance=budget)
        api_client.include_public_token(public_token)
        return budget
    return inner


@pytest.fixture
def template_public_case(api_client, user, create_template, create_budget,
        create_public_token):
    def inner():
        budget = create_budget(created_by=user)
        template = create_template(created_by=user)
        public_token = create_public_token(instance=budget)
        api_client.include_public_token(public_token)
        return template
    return inner


@pytest.fixture
def budget_another_public_case(api_client, user, create_budget,
        create_public_token):
    def inner():
        budget = create_budget(created_by=user)
        another_budget = create_budget(created_by=user)
        public_token = create_public_token(instance=another_budget)
        api_client.include_public_token(public_token)
        return budget
    return inner


@pytest.fixture
def logged_in_case(api_client, user, create_domain_budget):
    def inner(domain):
        budget = create_domain_budget(domain=domain, created_by=user)
        api_client.force_login(user)
        return budget
    return inner


@pytest.fixture
def not_logged_in_case(user, create_domain_budget):
    def inner(domain):
        return create_domain_budget(domain=domain, created_by=user)
    return inner


@pytest.fixture
def multiple_case(api_client, create_domain_budget, user):
    def inner(domain):
        create_domain_budget(domain=domain, created_by=user)
        budget = create_domain_budget(domain=domain, created_by=user)
        api_client.force_login(user)
        return budget
    return inner


@pytest.fixture
def budget_collaborator_case(api_client, user, create_user, create_budget,
        create_collaborator):
    def inner(info):
        budget = create_budget(created_by=user)
        collaborating_user = create_user()
        create_collaborator(
            access_type=info['access_type'],
            user=collaborating_user,
            instance=budget
        )
        api_client.force_login(collaborating_user)
        return budget
    return inner


@pytest.fixture
def budget_collaborator_not_logged_in_case(user, create_user, create_budget,
        create_collaborator):
    def inner(info):
        budget = create_budget(created_by=user)
        collaborating_user = create_user()
        create_collaborator(
            access_type=info['access_type'],
            user=collaborating_user,
            instance=budget
        )
        return budget
    return inner


@pytest.fixture
def establish_case(another_user_case, multiple_case, budget_another_public_case,
        budget_collaborator_case, logged_in_case, not_logged_in_case,
        budget_public_case, template_public_case,
        budget_collaborator_not_logged_in_case):
    def inner(domain, case, info):
        cases = {
            'another_user': lambda: another_user_case(domain),
            'not_logged_in': lambda: not_logged_in_case(domain),
            'logged_in': lambda: logged_in_case(domain),
            'multiple_budgets': lambda: multiple_case(domain),
            'public_case': lambda: {
                'budget': budget_public_case,
                'template': template_public_case
            }[domain](),
            'another_public_case': lambda: budget_another_public_case(),
            'collaborator': lambda: budget_collaborator_case(info),
            'collaborator_not_logged_in':
                lambda: budget_collaborator_not_logged_in_case(info)
        }
        return cases[case]()
    return inner


@pytest.fixture
def list_test_case(api_client, establish_case):
    def inner(domain, case):
        establish_case(domain, case, None)
        return api_client.get("/v1/%ss/" % domain)
    return inner


@pytest.fixture
def create_test_case(api_client, establish_case):
    def inner(domain, data, case):
        establish_case(domain, case, None)
        return api_client.post("/v1/%ss/" % domain, data=data)
    return inner


@pytest.fixture
def budget_detail_test_case(api_client, establish_case):
    def inner(domain, case, info, path="/"):
        budget = establish_case(domain, case, info)
        url = "/v1/budgets/%s%s" % (budget.pk, path)
        return api_client.get(url)
    return inner


@pytest.fixture
def budget_create_test_case(api_client, establish_case):
    def inner(domain, data, case, info, path="/"):
        budget = establish_case(domain, case, info)
        url = "/v1/budgets/%s%s" % (budget.pk, path)
        if hasattr(data, '__call__'):
            data = data(budget)
        return api_client.post(url, data=data)
    return inner


@pytest.fixture
def budget_update_test_case(api_client, establish_case):
    def inner(domain, data, case, info, path="/"):
        budget = establish_case(domain, case, info)
        url = "/v1/budgets/%s%s" % (budget.pk, path)
        return api_client.patch(url, data=data)
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


@pytest.mark.parametrize('case,info,assertions', [
    ('another_user', None, {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    ('not_logged_in', None, {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', None, {
        'status': lambda path: 401 if path == '/actuals/' else 200
    }),
    ('another_public_case', None, {'status': 401}),
    ('logged_in', None, {'status': 200}),
    ('multiple_budgets', None, {
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
    ('collaborator',
        {'access_type': Collaborator.ACCESS_TYPES.view_only},
        {'status': 200}
    ),
    ('collaborator',
        {'access_type': Collaborator.ACCESS_TYPES.owner},
        {'status': 200}
    ),
    ('collaborator',
        {'access_type': Collaborator.ACCESS_TYPES.editor},
        {'status': 200}
    ),
    ('collaborator_not_logged_in', {
        'access_type': Collaborator.ACCESS_TYPES.view_only},
        {'status': 401}
    ),
    ('collaborator_not_logged_in', {
        'access_type': Collaborator.ACCESS_TYPES.owner},
        {'status': 401}
    ),
    ('collaborator_not_logged_in', {
        'access_type': Collaborator.ACCESS_TYPES.editor},
        {'status': 401}
    ),
])
@pytest.mark.parametrize('path', [
    '/', '/children/', '/actuals/', '/fringes/', '/markups/', '/groups/'])
def test_budget_detail_read_permissions(case, info, path, assertions,
        budget_detail_test_case, make_assertions):
    response = budget_detail_test_case("budget", case, info, path)
    make_assertions(response, case, path, assertions)


@pytest.mark.parametrize('case,info,assertions', [
    ('another_user', None, {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    ('not_logged_in', None, {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', None, {'status': 401}),
    ('logged_in', None, {'status': 200}),
    ('multiple_budgets', None, {'status': 200})
])
@pytest.mark.parametrize('path', [
    '/', '/children/', '/fringes/', '/markups/', '/groups/'])
def test_template_detail_read_permissions(case, info, path, assertions,
        budget_detail_test_case, make_assertions):
    response = budget_detail_test_case("template", case, info, path)
    make_assertions(response, case, path, assertions)


@pytest.mark.parametrize('case,assertions', [
    ('not_logged_in', {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', {'status': 401}),
    ('logged_in', {'status': 200}),
    ('multiple_budgets', {'status': 200})
])
@pytest.mark.parametrize('domain', ['budget', 'template'])
def test_list_read_permissions(case, assertions, list_test_case, domain,
        make_assertions):
    response = list_test_case(domain, case)
    make_assertions(response, case, "/", assertions)


@pytest.mark.parametrize('case,info,assertions', [
    ('another_user', None, {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    ('not_logged_in', None, {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', None, {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('another_public_case', None, {'status': 401}),
    ('logged_in', None, {'status': 201}),
    ('multiple_budgets', None, {
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
    ('collaborator',
        {'access_type': Collaborator.ACCESS_TYPES.view_only},
        {'status': 403}
    ),
    ('collaborator',
        {'access_type': Collaborator.ACCESS_TYPES.owner},
        {'status': 201}
    ),
    ('collaborator',
        {'access_type': Collaborator.ACCESS_TYPES.editor},
        {'status': 201}
    ),
    ('collaborator_not_logged_in', {
        'access_type': Collaborator.ACCESS_TYPES.view_only},
        {'status': 401}
    ),
    ('collaborator_not_logged_in', {
        'access_type': Collaborator.ACCESS_TYPES.owner},
        {'status': 401}
    ),
    ('collaborator_not_logged_in', {
        'access_type': Collaborator.ACCESS_TYPES.editor},
        {'status': 401}
    ),
])
@pytest.mark.parametrize('path,data', [
    ('/children/', {}),
    ('/actuals/', {}),
    ('/fringes/', {}),
])
def test_budget_create_permissions(case, info, path, data, assertions,
        budget_create_test_case, make_assertions):
    response = budget_create_test_case("budget", data, case, info, path)
    make_assertions(response, case, path, assertions)


@pytest.mark.parametrize('case,info,assertions', [
    ('another_user', None, {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
    ('not_logged_in', None, {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('public_case', None, {'status': 401, 'error': {
        'message': 'User is not authenticated.',
        'code': 'account_not_authenticated',
        'error_type': 'auth'
    }}),
    ('another_public_case', None, {'status': 401}),
    ('logged_in', None, {'status': 201}),
    ('multiple_budgets', None, {
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
    ('collaborator',
        {'access_type': Collaborator.ACCESS_TYPES.view_only},
        {'status': 403}
    ),
    ('collaborator',
        {'access_type': Collaborator.ACCESS_TYPES.owner},
        {'status': 201}
    ),
    ('collaborator',
        {'access_type': Collaborator.ACCESS_TYPES.editor},
        {'status': 201}
    ),
    ('collaborator_not_logged_in', {
        'access_type': Collaborator.ACCESS_TYPES.view_only},
        {'status': 401}
    ),
    ('collaborator_not_logged_in', {
        'access_type': Collaborator.ACCESS_TYPES.owner},
        {'status': 401}
    ),
    ('collaborator_not_logged_in', {
        'access_type': Collaborator.ACCESS_TYPES.editor},
        {'status': 401}
    ),
])
def test_budget_create_groups_permissions(case, info, assertions,
        budget_create_test_case, make_assertions, create_budget_account):

    def post_data(budget):
        accounts = [create_budget_account(parent=budget)]
        return {'children': [a.pk for a in accounts], 'name': 'Test Group'}

    response = budget_create_test_case(
        "budget", post_data, case, info, '/groups/')
    make_assertions(response, case, '/groups/', assertions)


@pytest.mark.needtowrite
def test_budget_create_markups_permissions():
    pass


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
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
    ('logged_in', {'status': 201}),
    ('multiple_budgets', {'status': 201}),
])
@pytest.mark.parametrize('path,data', [
    ('/children/', {}),
    ('/fringes/', {}),
])
def test_template_create_permissions(case, path, data, assertions,
        budget_create_test_case, make_assertions):
    response = budget_create_test_case("template", data, case, None, path)
    make_assertions(response, case, path, assertions)


@pytest.mark.parametrize('case,assertions', [
    ('another_user', {'status': 403, 'error': {
        'message': 'The user must does not have permission to view this budget.',
        'code': 'permission_error',
        'error_type': 'permission'
    }}),
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
    ('logged_in', {'status': 201}),
    ('multiple_budgets', {'status': 201}),
])
def test_template_create_groups_permissions(case, assertions,
        budget_create_test_case, make_assertions, create_template_account):

    def post_data(budget):
        accounts = [create_template_account(parent=budget)]
        return {'children': [a.pk for a in accounts], 'name': 'Test Group'}

    response = budget_create_test_case(
        "template", post_data, case, None, '/groups/')
    make_assertions(response, case, '/groups/', assertions)


@pytest.mark.needtowrite
def test_template_create_markups_permissions():
    pass


def test_update_public_budget(api_client, create_budget, create_public_token):
    budget = create_budget()
    public_token = create_public_token(instance=budget)
    api_client.include_public_token(public_token)
    response = api_client.post("/v1/budgets/%s/" % budget.pk, data={
        'name': 'New Name'
    })
    assert response.status_code == 401


def test_create_budget_not_logged_in(api_client):
    response = api_client.post("/v1/budgets/", data={'name': 'New Name'})
    assert response.status_code == 401


def test_create_budget_with_public_token(api_client, create_public_token,
        create_budget):
    budget = create_budget()
    public_token = create_public_token(instance=budget)
    api_client.include_public_token(public_token)
    response = api_client.post("/v1/budgets/", data={'name': 'New Name'})
    assert response.status_code == 401


def test_create_additional_budget_unsubscribed(api_client, user, create_budget):
    create_budget()
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/", data={"name": "Test Name"})
    assert response.status_code == 403
    assert response.json() == {'errors': [{
        'message': "The user's subscription does not support multiple budgets.",
        'code': 'product_permission_error',
        'error_type': 'permission',
        'products': '__any__',
        'permission_id': 'multiple_budgets'
    }]}


def test_duplicate_budget_unsubscribed(api_client, user, create_budget):
    original = create_budget(created_by=user)
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/duplicate/" % original.pk)
    assert response.status_code == 403
    assert response.json() == {'errors': [{
        'message': "The user's subscription does not support multiple budgets.",
        'code': 'product_permission_error',
        'error_type': 'permission',
        'products': '__any__',
        'permission_id': 'multiple_budgets'
    }]}


def test_duplicate_template_unsubscribed(api_client, user, create_template):
    original = create_template(created_by=user)
    api_client.force_login(user)
    response = api_client.post("/v1/budgets/%s/duplicate/" % original.pk)
    assert response.status_code == 201
