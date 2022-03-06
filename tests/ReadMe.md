# Testing

Integrating a comprehensive testing suite is crucial for developing a robust and stable REST API.  This documentation
provides some background on the frameworks that our testing suite relies on in addition to some background on our specific
implementation of these frameworks.

## Testing Principles

Our testing suite abides by the following core principles:

1. Coverage Principle
2. Endpoint Principle
3. Abstraction Principle

### Coverage Principle

The Coverage Principle generally states that every consumer facing behavior of the API must have test coverage, without
exception. The way in which we go about covering those implementations with tests may vary, but there should not be
any exposed logic that does not have at least one test written for it.

### Endpoint Principle

The Endpoint Principle is a more specific form of the Coverage Principle.  The Endpoint Principle states that every
single endpoint that the API supports must have at least 1 end-to-end test written for it.  This means that there must
be at least 1 test that sends an API request to the endpoint and validates that the response is as expected.

The majority of test coverage comes from the extensive use of end-to-end testing of every single endpoint in the application.
Since the entrypoint of every single consumer facing behavior is a request to one of the endpoints our API supports, this
is a great way to ensure comprehensive test coverage across the API.

### Abstraction Principle

The Abstraction Principle states that tests should contain minimal to no abstraction.  The exceptions to this rule are mostly
concerned with the processes for generating test data that tests can use - where abstraction is acceptable if it makes sense.
However, abstraction around assertions of test results should be avoided at all costs.

The reasons for this are as follows:

1. Test abstraction makes it more difficult to diagnose failures, especially in remote environments, when tests fail.
2. We do not want to have to write tests for our tests.
3. Abstraction can confuse [pytest](https://docs.pytest.org/en/latest/contents.html#toc)'s ability to provide useful diagnostic information when tests fail.
4. Abstraction makes it more difficult to locate the specific assertion that caused a test to fail.

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

Tests should be as transparent and clear as possible so that they can be easily diagnosed and fixed.

## Frameworks

Our testing suite is a combination of the following frameworks:

1. [pytest](https://docs.pytest.org/en/latest/contents.html#toc): Provides the framework for creating and executing tests.
2. [pytest-django](https://pytest-django.readthedocs.io/en/latest/): Provides an integration for `pytest` with `Django`.
3. [coverage](https://coverage.readthedocs.io/en/v4.5.x/): Provides the framework for reporting on the project's test coverage and web integrations for viewing the test coverage of the project.

### Pytest

We use the [pytest](https://docs.pytest.org/en/latest/contents.html#toc) framework to develop a comprehensive testing suite across
our API.  [pytest](https://docs.pytest.org/en/latest/contents.html#toc) takes a functional approach to testing, and incorporates
an innovative concept called "fixtures" that enable common testing resources to be shared across tests.

#### Fixtures

The core concept that [pytest](https://docs.pytest.org/en/latest/contents.html#toc) provides is the notion of [fixtures](https://docs.pytest.org/en/latest/fixture.html) (not to be confused with Django fixtures, which are used to populate the
database from JSON files).  [Fixtures](https://docs.pytest.org/en/latest/fixture.html) are a set of resources that are setup
by the testing framework before a test starts and torn down after the test ends.

[Fixtures](https://docs.pytest.org/en/latest/fixture.html) are automatically loaded into memory by [pytest](https://docs.pytest.org/en/latest/contents.html#toc) when tests are run.  [pytest](https://docs.pytest.org/en/latest/contents.html#toc) will scan the root directory that the tests are located in for
any files (at the root or in any sub-directory) named `conftest.py`.  Any fixture in any `conftest.py` file is then loaded into memory and available
as a resource for all tests in the suite.

##### Example

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

```python
# tests/test_user.py

def test_resource(my_resource):
    assert my_resource.user.username == 'username'
    assert my_resource.read() == b'Some data'
```

##### Useful Fixtures

[pytest](https://docs.pytest.org/en/latest/contents.html#toc) comes with some fixtures out of the box.  Additionally, `pytest-django`
adds some useful fixtures as well.  Some notable/useful fixtures include:

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

In order to run the entire test suite, simply run the following bash command from the root of the repository:

```bash
$ pytest ./tests
```

This command will look inside the `tests` directory and recursively look for any Python file that whose name
is formatted as `test_*.py` or `*_test.py`.  For each of those files, it will run every test in the file.

##### Running Subsets of Tests

[pytest](https://docs.pytest.org/en/latest/contents.html#toc) provides the ability to run specific tests or subsets of
the testing suite from the command line.

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

[pytest](https://docs.pytest.org/en/latest/contents.html#toc) allows us to parameterize the execution of tests by
decorating test functions with parameterized inputs with a list of `(input, output)` tuples.  Each iteration over the parameterized
inputs counts as a discrete test.

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
raised.  This can be done as follows:

```python
import pytest
def test_expected_error():
    with pytest.raises(ZeroDivisionError):
        1/0
```

#### Skipping a Test

There are some cases where you might want to temporarily skip a test but leave
the code in place.  This can be done as follows:


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

`pytest-django` is a package that allows `pytest` to seamlessly integrate with Django.  The package provides many useful
fixtures and marks that allow your tests to interact with the database and other Django core functionality.

### Database Access

`pytest-django` takes a conservative approach to enabling database access.
By default your tests will fail if they try to access the database.
Only if you explicitly request database access will this be allowed.
This encourages you to keep database-needing tests to a minimum which is a best
practice since next-to-no business logic should be requiring the database.
Moreover it makes it very clear what code uses the database and catches any mistakes.

You can use pytest marks to tell `pytest-django` to allow database access:

```python
import pytest

@pytest.mark.django_db
def test_user():
    u = User.objects.create_superuser('user', 'user@email.com', 'password')
    assert u.is_superuser
```
