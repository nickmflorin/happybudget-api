# pylint: disable=redefined-outer-name
import copy
from os import access
import pytest

from greenbudget.app.collaborator.models import Collaborator


class PermissionCaseResponse:
    def __init__(self, response, url, case, method):
        self.response = response
        self.url = url
        self.case = case
        self.method = method

    @property
    def status_code(self):
        return self.response.status_code

    @classmethod
    def patch(cls, response, url, case):
        return cls(response, url, case, method="PATCH")

    @classmethod
    def post(cls, response, url, case):
        return cls(response, url, case, method="POST")

    @classmethod
    def get(cls, response, url, case):
        return cls(response, url, case, method="GET")

    @classmethod
    def delete(cls, response, url, case):
        return cls(response, url, case, method="DELETE")

    @property
    def status_assertion(self):
        if self.case.status is not None \
                and hasattr(self.case.status, '__call__'):
            return self.case.status(self.case)
        return self.case.status

    @property
    def error_assertion(self):
        if self.case.error is not None \
                and hasattr(self.case.error, '__call__'):
            return self.case.error(self.case)
        return self.case.error


class ParameterizedCase:
    def __init__(self, name, **kwargs):
        self.name = name
        # Maintain custom supplied attributes such that they can be accessed
        # through attribute lookup.
        self._kwargs = kwargs

        # Attributes that are used to make response assertions.
        self.status = kwargs.get('status', None)
        self.error = kwargs.get('error', None)

        # Attributes that are universally applicable.
        self.domain = kwargs.get('domain', 'budget')
        self.path = kwargs.get('path', '/')

    def __getattr__(self, k):
        if k == '__name__':
            return super().__getattr__(k)
        elif k not in self._kwargs:
            raise AttributeError("Case does not have attribute %s." % k)
        return self._kwargs[k]

    def with_info(self, **kwargs):
        kw = copy.deepcopy(self._kwargs)
        kw.update(**kwargs)
        return self.__class__(self.name, **kw)

    @classmethod
    def parameterize(cls, cases):
        flattened_cases = []
        for case in cases:
            if hasattr(case, '__iter__'):
                flattened_cases += case
            else:
                flattened_cases += [case]
        def decorator(func):
            return pytest.mark.parametrize('case', flattened_cases)(func)
        return decorator

    @classmethod
    def not_logged_in(cls, create=True):
        return cls(name='not_logged_in', status=401, create=create, error={
            'message': 'User is not authenticated.',
            'code': 'account_not_authenticated',
            'error_type': 'auth'
        })

    @classmethod
    def multiple_budgets_not_authenticated(cls):
        return cls('multiple_budgets', login=False, status=401, error={
            'message': 'User is not authenticated.',
            'code': 'account_not_authenticated',
            'error_type': 'auth'
        })

    @classmethod
    def multiple_budgets_restricted(cls):
        return cls('multiple_budgets', login=True, status=403, error={
            'message': (
                "The user's subscription does not support multiple budgets."),
            'code': 'product_permission_error',
            'error_type': 'permission',
            'products': '__any__',
            'permission_id': 'multiple_budgets'
        })

    @classmethod
    def _collaborator(cls, **kwargs):
        kwargs.setdefault('login', True)
        return ParameterizedCase('collaborator', **kwargs)

    @classmethod
    def collaborator(cls, **kwargs):
        access_type_names = ['view_only', 'owner', 'editor']
        assert 'status' in kwargs \
            or all([x in kwargs for x in access_type_names]), \
            "Either the expected status code must be provided or the expected " \
            "status code for each access type must be provided."
        return [
            cls._collaborator(
                access_type=Collaborator.ACCESS_TYPES.view_only,
                status=kwargs.get('view_only', kwargs.get('status'))
            ),
            cls._collaborator(
                access_type=Collaborator.ACCESS_TYPES.owner,
                status=kwargs.get('owner', kwargs.get('status'))
            ),
            cls._collaborator(
                access_type=Collaborator.ACCESS_TYPES.editor,
                status=kwargs.get('editor', kwargs.get('status'))
            ),
            cls._collaborator(
                login=False,
                access_type=Collaborator.ACCESS_TYPES.view_only,
                status=401
            ),
            cls._collaborator(
                login=False,
                access_type=Collaborator.ACCESS_TYPES.owner,
                status=401
            ),
            cls._collaborator(
                login=False,
                access_type=Collaborator.ACCESS_TYPES.editor,
                status=401
            )
        ]


@pytest.fixture
def base_url():
    raise NotImplementedError(
        "This fixture must be defined in the permission test file in order to "
        "properly test permissions."
    )


@pytest.fixture
def create_obj():
    raise NotImplementedError(
        "This fixture must be defined in the permissions test file such that "
        "the permission cases know how to create the object they are testing "
        "permissions for."
    )


@pytest.fixture
def objless_url(base_url, establish_case):
    def inner(case):
        establish_case(case)
        assert not hasattr(case.path, '__call__'), \
            "The path may only be a callable when the endpoint is a detail " \
            "endpoint."
        base = base_url
        if hasattr(base, '__call__'):
            base = base(case)
        path = case.path if not case.path.startswith('/') else case.path[1:]
        return "%s%s" % (base, path)
    return inner


@pytest.fixture
def obj_url(base_url, establish_case):
    def inner(case):
        obj = establish_case(case)
        path = case.path
        if hasattr(path, '__call__'):
            path = path(obj)
        base = base_url
        if hasattr(base_url, '__call__'):
            base = base_url(case, obj=obj)
        return "%s%s%s" % (base, obj.pk, path), obj
    return inner


@pytest.fixture
def logged_in_case(api_client, user, f, create_obj):
    def inner(case):
        api_client.force_login(user)
        if getattr(case, 'create', False) is True:
            budget = f.create_budget(domain=case.domain, created_by=user)
            return create_obj(budget, case)
        return None
    return inner


@pytest.fixture
def logged_in_staff_user_case(api_client, user, staff_user, f, create_obj):
    def inner(case):
        api_client.force_login(staff_user)
        if getattr(case, 'create', False) is True:
            budget = f.create_budget(domain=case.domain, created_by=user)
            return create_obj(budget, case)
        return None
    return inner


@pytest.fixture
def not_logged_in_case(user, f, create_obj):
    def inner(case):
        if getattr(case, 'create', False) is True:
            budget = f.create_budget(domain=case.domain, created_by=user)
            return create_obj(budget, case)
        return None
    return inner


@pytest.fixture
def another_user_case(api_client, user, f, create_obj):
    def inner(case):
        another_user = f.create_user()
        # Log the user in that will not be used to create the base budget.
        api_client.force_login(user)
        budget = f.create_budget(domain=case.domain, created_by=another_user)
        return create_obj(budget, case)
    return inner


@pytest.fixture
def public_case(api_client, user, f, create_obj):
    def inner(case):
        # Regardless of what domain we are in, always use a Budget as the basis
        # of the PublicToken.
        budget = f.create_budget(created_by=user)
        public_token = f.create_public_token(instance=budget)
        api_client.include_public_token(public_token)

        # If we are in the `budget` domain, we can simply return the Budget
        # associated with the PublicToken.  Otherwise, we return the Template,
        # which isn't associated with the PublicToken - but the PublicToken is
        # still on the request (which is what we are testing).
        if case.domain == 'budget':
            return create_obj(budget, case)
        return create_obj(f.create_template(created_by=user), case)
    return inner


@pytest.fixture
def another_public_case(api_client, user, f, create_obj):
    def inner(case):
        # The `template` domain is never applicable here, because we are testing
        # whether or not the PublicToken attached to the request is associated
        # with the correct Budget.  This test would be pointless in the Template
        # domain, because the Budget associated with the PublicToken would never
        # be a Template.
        assert case.domain == 'budget', \
            "Another public case case can only be used on the budget domain."

        budget = f.create_budget(created_by=user)
        # Create another budget that will be associated with the PublicToken.
        another_budget = f.create_budget(created_by=user)
        public_token = f.create_public_token(instance=another_budget)
        api_client.include_public_token(public_token)

        return create_obj(budget, case)
    return inner


@pytest.fixture
def multiple_case(api_client, f, user, create_obj):
    def inner(case):
        if getattr(case, 'login', True) is True:
            api_client.force_login(user)
        # Create the first Budget that belongs to the User in the domain that is
        # associated with the case.
        f.create_budget(domain=case.domain, created_by=user)
        # The subsequent objects should be created with respect to an additional
        # Budget.
        return create_obj(
            f.create_budget(domain=case.domain, created_by=user),
            case
        )
    return inner


@pytest.fixture
def collaborator_case(api_client, user, f, create_obj):
    def inner(case):
        assert case.domain == 'budget', \
            "Collaborator case can only be used on the budget domain."

        budget = f.create_budget(created_by=user)
        collaborating_user = f.create_user()
        if getattr(case, 'login', True) is True:
            api_client.force_login(collaborating_user)
        f.create_collaborator(
            access_type=case.access_type,
            user=collaborating_user,
            instance=budget
        )
        return create_obj(budget, case)
    return inner


@pytest.fixture
def cases(another_user_case, multiple_case, another_public_case,
        collaborator_case, logged_in_case, not_logged_in_case,
        public_case, logged_in_staff_user_case):
    return {
        'another_user': another_user_case,
        'not_logged_in': not_logged_in_case,
        'logged_in': logged_in_case,
        'logged_in_staff': logged_in_staff_user_case,
        'multiple_budgets': multiple_case,
        'public_case': public_case,
        'another_public_case': another_public_case,
        'collaborator': collaborator_case,
    }


@pytest.fixture
def establish_case(cases):
    def inner(parameterized_case):
        if parameterized_case.name not in cases:
            raise LookupError(
                "There is no case registgered with name "
                f"{parameterized_case.name}."
            )
        return cases[parameterized_case.name](parameterized_case)
    return inner


@pytest.fixture
def with_assertion(make_permission_assertions):
    def inner(func):
        def decorated(case, **kwargs):
            make_assertion = kwargs.pop('make_assertion', True)
            response = func(case, **kwargs)
            if make_assertion:
                make_permission_assertions(response)
            return response
        return decorated
    return inner


@pytest.fixture
def update_response(api_client, obj_url, with_assertion):
    @with_assertion
    def inner(case, **kwargs):
        case = case.with_info(method='PATCH', **kwargs)
        url, _ = obj_url(case)
        return PermissionCaseResponse.patch(
            response=api_client.patch(url, data=case.data),
            url=url,
            case=case
        )
    return inner


@pytest.fixture
def detail_response(api_client, obj_url, with_assertion):
    @with_assertion
    def inner(case, **kwargs):
        case = case.with_info(method='GET', **kwargs)
        url, _ = obj_url(case)
        return PermissionCaseResponse.get(
            response=api_client.get(url),
            url=url,
            case=case
        )
    return inner


@pytest.fixture
def list_response(api_client, objless_url, with_assertion):
    @with_assertion
    def inner(case, **kwargs):
        case = case.with_info(method='GET', **kwargs)
        url = objless_url(case)
        return PermissionCaseResponse.get(
            response=api_client.get(url),
            url=url,
            case=case
        )
    return inner


@pytest.fixture
def create_response(api_client, objless_url, with_assertion):
    @with_assertion
    def inner(case, **kwargs):
        case = case.with_info(method='POST', **kwargs)
        url = objless_url(case)

        data = getattr(case, 'data', None)
        assert not hasattr(data, '__call__'), \
            "The data may only be a callable when the endpoint is a detail " \
            "endpoint."

        return PermissionCaseResponse.post(
            response=api_client.post(url, data=data),
            url=url,
            case=case
        )
    return inner


@pytest.fixture
def delete_response(api_client, obj_url, with_assertion):
    @with_assertion
    def inner(case, **kwargs):
        case = case.with_info(method='DELETE', **kwargs)
        url, _ = obj_url(case)
        return PermissionCaseResponse.delete(
            response=api_client.delete(url),
            url=url,
            case=case
        )
    return inner


@pytest.fixture
def detail_create_response(api_client, obj_url, with_assertion):
    @with_assertion
    def inner(case, **kwargs):
        case = case.with_info(method='POST', **kwargs)
        url, obj = obj_url(case)
        data = getattr(case, 'data', None)
        if hasattr(data, '__call__'):
            data = data(obj)
        return PermissionCaseResponse.post(
            response=api_client.post(url, data=data),
            url=url,
            case=case
        )
    return inner


@pytest.fixture
def detail_update_response(api_client, obj_url, with_assertion):
    @with_assertion
    def inner(case, **kwargs):
        case = case.with_info(method='PATCH', **kwargs)
        url, obj = obj_url(case)
        data = getattr(case, 'data', None)
        if hasattr(data, '__call__'):
            data = data(obj)
        r = api_client.patch(url, data=data)
        return PermissionCaseResponse.patch(
            response=api_client.patch(url, data=data),
            url=url,
            case=case
        )
    return inner


@pytest.fixture
def make_permission_assertions(assert_response_errors):
    def status_assertion_message(response, expected_status_code):
        return (
            f"The expected status code for {response.method} to {response.url} "
            f"(case {response.case.name}) was {expected_status_code}, "
            f"but the response had status code {response.status_code}."
        )

    def inner(response):
        if response.status_assertion:
            assert response.status_code == response.status_assertion, \
                status_assertion_message(response, response.status_assertion)
        if response.error_assertion:
            assert_response_errors(
                response.response,
                response.error_assertion,
                url=response.url,
                method=response.method
            )
    return inner
