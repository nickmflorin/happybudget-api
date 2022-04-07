# Testing

Integrating a comprehensive testing suite is crucial for developing a robust and
stable REST API. This documentation provides some background on the frameworks
that our testing suite relies on in addition to some background on our specific
implementation of these frameworks.

## Environment

Our testing suite has it's own dedicated environment in which to operate.

**Environment**
: `test`

**Settings Module**
: `greenbudget.conf.settings.test`

**File Storage**
: Temporary File Storage

**Database**
: Transactional SQLite3 File

## Testing Principles

Our testing suite abides by the following core principles:

1. Coverage Principle
2. Endpoint Principle
3. Abstraction Principle

### Coverage Principle

The Coverage Principle generally states that every consumer facing behavior of
the API must have test coverage, without exception. The way in which we go about
covering those implementations with tests may vary, but there should not be
any exposed logic that does not have at least one test written for it.

### Endpoint Principle

The Endpoint Principle is a more specific form of the Coverage Principle. The
Endpoint Principle states that every single endpoint that the API supports must
have at least 1 end-to-end test written for it. This means that there must be
at least 1 test that sends an API request to the endpoint and validates that the
response is as expected.

The majority of test coverage comes from the extensive use of end-to-end testing
of every single endpoint in the application. Since the entrypoint of every single
consumer facing behavior is a request to one of the endpoints our API supports,
this is a great way to ensure comprehensive test coverage across the API.

#### Example

In this example, we test the behavior of the endpoint responsible for retrieving
information about a specific Fringe at `/v1/fringes/<pk>/`:

```python
def test_get_fringe(api_client, user, budget_f, create_fringe, models):
    api_client.force_login(user)
    budget = budget_f.create_budget()
    fringe = create_fringe(budget=budget)
    response = api_client.get("/v1/fringes/%s/" % fringe.pk)
    assert response.status_code == 200
    assert response.json() == {
        "id": fringe.pk,
        "type": "fringe",
        "name": fringe.name,
        "description": fringe.description,
        "rate": fringe.rate,
        "cutoff": fringe.cutoff,
        "color": None,
        "order": "n",
        "unit": {
            "id": fringe.unit,
            "name": models.Fringe.UNITS[fringe.unit].name,
            "slug": models.Fringe.UNITS[fringe.unit].slug
        },
    }
```

Our endpoint tests follow this pattern, in the sense that we typically try to
test the entire output of the API call. The exceptions to this are when we
are testing other behaviors of an endpoint (like error handling) and the full
output of the successful API response (**200**, **201** or **204** status codes)
has already been tested in a separate test.

> Note that before we make an assertion about the response JSON, we make an
> assertion about the response status code. This is because if the response
> were not a **200** response, the test failure is easier to diagnose when the
> assertion for the response status code fails vs. a failure of the assertion
> regarding the response JSON.

### Abstraction Principle

The Abstraction Principle states that tests should contain minimal to no
abstraction. The exceptions to this rule are mostly concerned with the processes
for generating test data that tests can use - where abstraction is acceptable if
it makes sense. However, abstraction around assertions of test results should be
avoided at all costs.

The reasons for this are as follows:

1. Test abstraction makes it more difficult to diagnose failures, especially in
   remote environments, when tests fail.
2. We do not want to have to write tests for our tests.
3. Abstraction can confuse [pytest](https://docs.pytest.org/en/latest/contents.html#toc)'s
   ability to provide useful diagnostic information when tests fail.
4. Abstraction makes it more difficult to locate the specific assertion that
   caused a test to fail.

#### Example

This is an example of a bad abstraction in a test:

```python
@pytest.fixture
def assert_response_ok():
    def inner(response):
        assert response.status_code == 200
        assert response.json() != {}
    return inner

def test_get_document(api_client, assert_response_ok):
    response = api_client.get("/v1/budgets/5/")
    assert_response_ok(response)
```

Tests should be as transparent and clear as possible so that they can be easily
diagnosed and fixed.

## Frameworks

Our testing suite is a combination of the following frameworks:

1. [pytest](https://docs.pytest.org/en/latest/contents.html#toc): Provides the
   framework for creating and executing tests.
2. [pytest-django](https://pytest-django.readthedocs.io/en/latest/): Provides an
   integration for `pytest` with `Django`.
3. [coverage](https://coverage.readthedocs.io/en/v4.5.x/): Provides the framework
   for reporting on the project's test coverage and web integrations for viewing
   the test coverage of the project.

### Pytest

We use the [pytest](https://docs.pytest.org/en/latest/contents.html#toc)
framework to develop a comprehensive testing suite across our API.
[pytest](https://docs.pytest.org/en/latest/contents.html#toc) takes a functional
approach to testing, and incorporates an innovative concept called "fixtures"
that enable common testing resources to be shared across tests.

#### Fixtures

The core concept that [pytest](https://docs.pytest.org/en/latest/contents.html#toc)
provides is the notion of [fixtures](https://docs.pytest.org/en/latest/fixture.html)
(not to be confused with Django fixtures, which are used to populate the database
from JSON files). [Fixtures](https://docs.pytest.org/en/latest/fixture.html) are
a set of resources that are setup by the testing framework before a test starts
and torn down after the test ends.

[Fixtures](https://docs.pytest.org/en/latest/fixture.html) are automatically
loaded into memory by [pytest](https://docs.pytest.org/en/latest/contents.html#toc)
when tests are run. [pytest](https://docs.pytest.org/en/latest/contents.html#toc)
will scan the root directory that the tests are located in for any files (at the
root or in any sub-directory) named `conftest.py`. Any fixture in any
`conftest.py` file is then loaded into memory and available as a resource for
all tests in the suite.

##### Example

In this example, we create a `my_user` fixture and a `my_resource` fixture
that are accessible as resources for all tests. The `my_resource` fixture
opens `SomeResource`, runs the test with the yielded `resource` and then
closes the `resource` after the test completes.

```python
# tests/conftest.py
import pytest

@pytest.fixture
def my_user():
    return User.objects.create(username='name', email='me@example.com')

@pytest.fixture
def my_resource(my_user):
    resource = SomeResource(user=my_user)
    resource.open()
    yield resource
    resource.close()
```

Here, the test `test_resource` accesses the fixture `my_resource`. Once the
test finishes, the `SomeResource` instance associated with the `my_resource`
fixture is closed.

```python
# tests/test_user.py

def test_resource(my_resource):
    assert my_resource.user.username == 'username'
    assert my_resource.read() == b'Some data'
```

##### Useful Fixtures

[pytest](https://docs.pytest.org/en/latest/contents.html#toc) comes with some
fixtures out of the box. Additionally, `pytest-django` (which is documented in
the next section) adds some useful fixtures as well.

Some notable/useful fixtures include:

- `capsys`: Captures stdout/stderr output
- `tmp_path`: Returns a created temporary path unique to the test invocation
- `rf`: instance of `django.test.RequestFactory`
- `client`: instance of `django.test.Client`
- `django_user_model`: Shortcut to the user model (`settings.AUTH_USER_MODEL`)
- `admin_client`: A `client` instance with a logged in admin user.
- `admin_user`: Instance of a superuser.
- `settings`: A handle on the Django settings module, and automatically revert
  any changes made to the settings (modifications, additions and deletions)
- [All default fixtures](https://docs.pytest.org/en/latest/reference.html#fixtures)

#### Running Tests

In order to run the entire test suite, simply run the following bash command
from the root of the repository:

```bash
$ pytest ./tests
```

This command will look inside the `tests` directory and recursively look for any
Python file that whose name is formatted as `test_*.py` or `*_test.py`. For each
of those files, it will run every test in the file.

##### Running Subsets of Tests

[pytest](https://docs.pytest.org/en/latest/contents.html#toc) provides the
ability to run specific tests or subsets of the testing suite from the command
line.

###### Running all tests within a specific file:

```bash
$ pytest tests/test_config.py
```

###### Running a specific test function in a specific file:

```bash
$ pytest tests/test_config.py::test_my_function
```

###### Running a specific test class in a specific file:

```bash
$ pytest tests/test_tests.py::TestClass
```

###### Running a specific test method on a test class in a specific file:

```bash
$ pytest tests/test_tests.py::TestClass::test_my_method
```

#### Parameterizing Tests

[pytest](https://docs.pytest.org/en/latest/contents.html#toc) allows us to
parameterize the execution of tests by decorating test functions with
parameterized inputs with a list of `(input, output)` tuples. Each iteration over
the parameterized inputs counts as a discrete test.

##### Example

```python
import pytest

def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

@pytest.mark.parametrize('n, expected', [
    (0, 0),
    (1, 1),
    (2, 1),
    (3, 2),
    (4, 3),
    (5, 5),
    (6, 8),
    (7, 13)
])
def test_params(n, expected):
    assert fib(n) == expected
```

When the previous test code is run, `pytest` will actually run 8 discrete tests.

#### Asserting That an Exception was Raised

There are some cases where you might want to assert that an `Exception` was
raised. This can be done as follows:

```python
import pytest
def test_expected_error():
    with pytest.raises(ZeroDivisionError):
        1/0
```

#### Skipping a Test

There are some cases where you might want to temporarily skip a test but leave
the code in place. This can be done as follows:

```python
@pytest.mark.skip(reason="no way of currently testing this")
def test_skippable():
    ...
```

#### Expected Failures

There are some cases where you want to intentionally allow and assert that a
specific test fails.

##### Example

```python
@pytest.mark.xfail
def test_function():
    ...
```

or:

```python
def test_function(condition):
    if condition.is_set:
        pytest.xfail("Condition is set.")
```

### pytest-django

`pytest-django` is a package that allows `pytest` to seamlessly integrate with
Django. The package provides many useful fixtures and marks that allow your
tests to interact with the database and other Django core functionality.

#### Database Access

`pytest-django` takes a conservative approach to enabling database access.
By default your tests will fail if they try to access the database. Only if you
explicitly request database access will this be allowed.

You can use pytest marks to tell `pytest-django` to allow database access:

```python
import pytest

@pytest.mark.django_db
def test_user():
    u = User.objects.create_superuser('user', 'user@email.com', 'password')
    assert u.is_superuser
```

Additionally, including the `db` fixture will also tell `pytest-django` to allow
database access:

```python
@pytest.fixture
def user(db, user_password):
    user = User.objects.create(...)
    user.set_password(user_password)
    user.save()
    return user
```

> Note that all of our factory fixtures use the `db` fixture by default, so when
> creating data from factories we do not need to include the `db` fixture in
> the specific test.

## Test Suite

This section discusses the frameworks that have been built around `pytest` and
`pytest-django` to more specifically accomodate our use cases.

### Marks

[pytest](https://docs.pytest.org/en/latest/contents.html#toc) marks are used to
control how a test is run by "tagging" the test method in a way that we can
manipulate it's behavior in certain fixtures that
[pytest](https://docs.pytest.org/en/latest/contents.html#toc) reserves for this
purpose.

Our testing suite incorporates the following custom marks that we can use for
debugging and/or notification purposes:

1. `pytest.mark.budget`: Instructs the test to only run for the "budget" domain.
2. `pytest.mark.template`: Instructs the test to only run for the "template" domain.
3. `pytest.mark.needtowrite`: Instructs `pytest` to skip the test and issue a
   warning that the test needs to be written.
4. `pytest.mark.postgresdb`: Instructs `pytest` that this test will use a
   Postgres database and should be skipped unless that is the database in use.

### API Requests

Django REST Framework exposes a client `rest_framework.test.APIClient` (which
is just a lightweight wrapper around Django's `django.test.client.Client`
tailored towards the `rest_framework` package) that can be used to make API
requests in tests.

Our test suite wraps `rest_framework.test.APIClient` very minimally in order to
provide some additional behavior, and exposes the client as a
[pytest](https://docs.pytest.org/en/latest/contents.html#toc) fixture,
`api_client`.

> Note: Django REST Framework's test client, `rest_framework.test.APIClient`
> will automatically bypass CSRF checks.

#### Logging User In

To log the user in before making an API request in a test, simply use the
`force_login` method:

```python
def test_get_account(api_client, user, budget_f):
    budget = budget_f.create_budget()
    account = budget_f.create_account(parent=budget)
    api_client.force_login(user)
    ...
```

#### Submitting a Request

To submit an HTTP request in a test, simply call the appropriate `get`, `post`,
`patch`, `delete` or `put` method on the test client:

```python
def test_get_account(api_client, user, budget_f):
    ...
    response = api_client.get("/v1/accounts/%s/" % account.pk)
```

### Data Generation

All tests rely on a source of test data to allow the logic in the application
to be tested in as close to a production environment as possible. There are
many different approaches for providing a testing suite with test data, varying
from using an entirely separate database with preloaded data to generating the
data on the fly on a test-by-test basis.

Our testing suite uses the approach of creating data entities are they are
needed by each individual test, and removing them after the test completes. The
primary motivation for this approach was to ensure that tests are entirely
independent of one another, and each test can alter the database as it sees fit
without disrupting other tests in the testing suite.

#### Factories

In order to allow each test to generate data that it needs to run the test, we
use "factories" that are then exposed as fixtures for each test.

A factory is a partial implementation of a Django model that instructs the
testing suite how to create instances of the model with dummy data.

##### Example

For example, the following factory is used to generate instances of the `Fringe`
model. All static properties on the factory class instruct the framework how
to randomly or deterministically generate data for that field of the model -
unless the field value is explicitly provided to the factory.

```python
class FringeFactory(CustomModelFactory):
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Fringe {n}")
    description = factory.Faker('sentence')
    cutoff = None
    rate = 1.00
    unit = Fringe.UNITS.percent

    class Meta:
        model = Fringe
```

In the above, for example, unless we explicitly provide the `description` field
to `FringeFactory` the `FringeFactory` will create a `Fringe` instance with
a randomly generated sentence as the `description`.

The factory can then be used as follows:

```python
def test_fringe(user):
    test_fringe = FringeFactory(created_by=user, updated_by=user, rate=20.0)
    assert fringe.rate == 20.0
    assert fringe.name == "Fringe 1"
    assert fringe.cutoff is None
    assert fringe.unit == Fringe.UNITS.percent
```

> Note that factory.SubFactory will use a factory to randomly generate the field
> if that field is a `ForeignKey` pointing to a Django model. In this case,
> unless the `created_by` and/or `updated_by` fields are provided explicitly,
> the `FringeFactory` will randomly generated a `User` with the `UserFactory`
> and assign it to those fields.

Implementing a factory framework for all of our models allows our tests to
quickly and conveniently create test data that it requires without having to
worry about providing every individual field that may not be relevant to test
at hand.

#### Factory Fixtures

As previously stated, all factories are exposed in our tests as fixtures. These
fixtures, which are all functions that eventually call the factory, wrap the
logic that each factory provides such that other business logic can be
incorporated via features of the
[pytest](https://docs.pytest.org/en/latest/contents.html#toc) ecosystem.

This means that in our tests, we do not directly import the factory classes
themselves. Instead, we use [pytest](https://docs.pytest.org/en/latest/contents.html#toc)
fixtures that we have created that wrap the factory class such that it can be
used as a [pytest](https://docs.pytest.org/en/latest/contents.html#toc) fixture
and has access to the resources of the
[pytest](https://docs.pytest.org/en/latest/contents.html#toc) ecosystem.

##### Example

For example, here we specify a `create_user` fixture that allows each test to
dynamically create a random user:

```python
@pytest.fixture
def create_user(db):
    def inner(*args, **kwargs):
        return factories.UserFactory(*args, **kwargs)
    return inner
```

There are several common patterns that our factories fixtures implement that
provide additional behavior that simple usage of factory classes in the tests
would not provide alone. Some of these are:

1. Establishing Ownership
2. Enabling Multiple Creation

##### Establishing Ownership

Many of our models are designated ownership by the field `created_by`.
Additionally, many of our models also track the user that last updated the
model instance via the `updated_by` field. These fields are always required
when creating a model instance if it is attributed with those fields.

Wrapping our factories in fixtures instead of using them outside of a fixture
scope gives us the convenience of not having to manually provide the
`created_by` and/or `updated_by` fields for many models that are attributed with
these fields. The factory fixtures will, by default, use the `User` returned
from the default `user` fixture to dictate ownership of the model instance:

```python
# tests/factories.py

@pytest.fixture
def create_budget(user):
    def inner(*args, **kwargs):
        kwargs.setdefault('created_by', user)
        return factories.BudgetFactory(*args, **kwargs)
    return inner
```

```python
# tests/budget/test_api.py

@pytest.mark.freeze_time('2020-01-01')
def test_get_budget(api_client, user, create_budget):
    budget = create_budget()
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/" % budget.pk)
    assert response.status_code == 200
    assert response.json() == {...}
```

If we were to use the `factories.BudgetFactory` outside the scope of a
fixture, we would have to explicitly define the `created_by` field each time.

##### Enabling Multiple Creation

There are many cases in our tests where we want to be able to quickly create
several instances of a model, not just one. In most cases, our factory fixtures
support this via the `allow_multiple` decorator.

This decorator allows a factory fixture to include a `count` parameter, that
indicates the number of instances that should be created. In this case, a
list of instances is returned instead of just the one instance.

When attributes are included to the factory fixture and the `count` parameter
is used, those attributes are applied to all created instances.

```python
def test_get_accounts(api_client, user, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(parent=budget, count=2)
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [...]
```

Here, we created 2 different `Account` instances, each with the same `parent`.

If the intention is to specify an attribute for each of the instances, the
attribute can be included as an iterable of attributes - where the iterable has
a length equal to `count`. The attributes from the iterable will be mapped to
each instance being created:

```python
def test_get_accounts(api_client, user, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(
        parent=budget,
        count=2,
        identifier=["0001", "0002"]
    )
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'][0]['identifier'] == '0001'
    assert response.json()['data'][1]['identifier'] == '0002'
```

#### Budgeting

In the code for this application, "Budgeting" refers to the models that make
up the core "tree" of a `Budget` or `Template`. That is, "Budgeting" refers
to extensions of `BaseBudget`, `Account` and `SubAccount`. The budget "tree"
refers to the nested parent-child relationships between the extensions of
`BaseBudget`, `Account` and `SubAccount`.

The "domain" of a budget "tree" refers to whether or not the tree is based on
a `Budget` or a `Template` instance. The models that make up the ancestry
"tree" of the budget are dictated by what the model is at the top of the tree
(the `Budget` or a `Template`).

| Domain or Base | BudgetModel  |   Account Model   |  Sub Account Model   |
| :------------: | :----------: | :---------------: | :------------------: |
|      base      | `BaseBudget` |     `Account`     |     `SubAccount`     |
|     budget     |   `Budget`   |  `BudgetAccount`  |  `BudgetSubAccount`  |
|    template    |  `Template`  | `TemplateAccount` | `TemplateSubAccount` |

Instead of exposing fixtures for all budgeting related models of each domain,
we simply expose them as an object that exposes methods to create the budgeting
models for the appropriate domain.

The two factory objects are exposed as the following fixtures:

1. `budget_df`: Read as "Budget Domain Factory". Exposes methods to create
   budgeting related models for the "budget" domain.
2. `template_df`: Read as "Template Domain Factory". Exposes methods to create
   budgeting related models for the "template" domain.

Each of these factory objects exposes the following methods:

1. `create_budget`: Creates a `Budget` or `Template`, depending on the factory
   object.
2. `create_account`: Creates a `BudgetAccount` or a `TemplateAccount`, depending
   on the factory object.
3. `create_subaccount`: Creates a `BudgetSubAccount` or a `TemplateSubAccount`,
   depending on the factory object.

##### Example

In this example, we are testing whether or not a `Budget`'s actual value is
recalculated after it's child `BudgetAccount` is deleted. Since actuals are
only applicable for the "budget" domain, we use the `budget_df` fixture:

```python
# tests/account/test_signals.py

def test_delete_account_reactualizes(budget_df, create_actual):
    budget = budget_df.create_budget()
    account = budget_df.create_account(parent=budget)
    parent_subaccount = budget_df.create_subaccount(parent=account)
    subaccount = budget_df.create_subaccount(
        parent=parent_subaccount,
        rate=1,
        multiplier=5,
        quantity=10,
    )
    create_actual(owner=subaccount, budget=budget, value=100.0)
    account.delete()
    assert budget.actual == 0.0
```

In this example, the root of the "budget" tree is the `budget`. The `budget`
instance than has the `account` as a child, the `account` has the
`parent_subaccount` as a child and the `parent_subaccount` has the `subaccount`
as a child. These relationships comprise the budget "tree".

Up until this point, the usage of `budget_df` and `template_df` has been purely
for convenience purposes - as it saves us the time of having to use the
`BaseBudget`, `Account` and `SubAccount` factory fixtures for the specific
domain we are interested in.

However, there is one very powerful implementation that is derived from this:
the `budget_f` fixture.

When used by a test, the `budget_f` fixture will automatically cause the test
to run 2 times, once for each domain. That is, it will run the entire test
where all budgeting related models are created for the "budget" domain, and also
run the entire test where all budgeting related models are created for the
"template" domain. Using the `budget_f` fixtures in our test gives us very, very
exhaustive test coverage.

##### Example

In this example, we use the `budget_f` fixture to test the
`/v1/budgets/<pk>/children/` endpoint in the case that the budget is both a
`Budget` **and** a `Template`:

```python
# tests/budget/test_account_api.py

def test_get_accounts(api_client, user, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(parent=budget, count=2)
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [...]
```

This test will generate 2 different discrete tests, one for each domain.

##### Marks

Usage of the `budget_f` factory object inspired two different
[pytest](https://docs.pytest.org/en/latest/contents.html#toc) marks for
debugging purposes. These are `pytest.mark.budget` and `pytest.mark.template`.
When these marks are used, they will restrict the test method to a specific
domain regardless of the usage of the `budget_f` factory object.

###### Example

In this example, we decorate the test method that uses the `budget_f` fixture
with `pytest.mark.budget` - which means it will only run for the budget domain.

```python
# tests/budget/test_account_api.py

@pytest.mark.budget
def test_get_accounts(api_client, user, budget_f):
    budget = budget_f.create_budget()
    accounts = budget_f.create_account(parent=budget, count=2)
    api_client.force_login(user)
    response = api_client.get("/v1/budgets/%s/children/" % budget.pk)
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['data'] == [...]
```

These marks should only be used for debugging purposes, when we want to quickly
restrict the domain of the test such that we can diagnose a test failure more
easily.

### Database Control

Our testing framework relies on the concept of "transactional testing". What this
means is that each test is run with an entirely fresh state of the database.
This is very important because it ensures that tests are completely independent
of one another, and updating the database in one test does not affect the behavior
of a subsequent test.

By default, our testing framework relies on an `sqlite` database. The reasons
for this are as follows:

1. `sqlite` databases make it easy and **fast** to quickly setup and tear down
   the database for each test, allowing us to use transactional tests while at
   the same time allowing the tests to run very fast.
2. `sqlite` requires less setup and configuration than a Postgres database.
3. `sqlite` does not require us to have a process dedicated to the Postgres
   database running in the background.

There are however cases where we may want to run specific tests with a Postgres
database. There are some not so subtle differences between a Postgres and
`sqlite` database that may factor into our tests, particularly as it relates to
concurrent requests. Fortunately, our testing framework allows for this
behavior.

#### Marks

In order to run a test using a Postgres database, we have a dedicated
[pytest](https://docs.pytest.org/en/latest/contents.html#toc) mark that informs
our testing suite that the test being run should use a Postgres database.

This mark, `pytest.mark.postgresdb` must be used in conjunction with the
[pytest-django](https://pytest-django.readthedocs.io/en/latest/) mark,
`@pytest.mark.django_db(transaction=True)` so that the testing suite properly
uses the Postgres database and treats the database in a transactional test
context.

##### Example

```python
@pytest.mark.postgresdb
@pytest.mark.django_db(transaction=True)
def test_bulk_create_subaccount_subaccounts_concurrently():
    ...
```

#### Running Tests

By default, when running tests all of the tests that are marked with
`@pytest.mark.postgresdb` will be skipped. This is because the tests using
a Postgres database must be run completely separately from the tests using the
`sqlite` database.

In order to run a test that is marked with `@pytest.mark.postgresdb`, we have
to run the tests from the command line with the `--postgresdb` flag.

###### Example

```bash
$ pytest ./tests/subaccount/test_concurrency.py --postgresdb
```

When the `--postgresdb` flag is used, all tests that are not marked with
`@pytest.mark.postgresdb` will be skipped, and only the tests that do include
this mark will be run.

> Note: Postgres is tricky to operate in a transactional test context because
> many times the connections and databases are not fully closed out and deleted
> at the end of a test. For this reason, running tests using a Postgres database
> often times requires manual setup and maintenance from the user running the
> tests in order to properly run in a transactional test context. This often
> times requires restarting the Postgres server, or ignoring the fact that the
> database may already exist when the test starts.
