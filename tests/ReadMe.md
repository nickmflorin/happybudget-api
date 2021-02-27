# Testing

Our testing framework is a combination of

1. [pytest](https://docs.pytest.org/en/latest/contents.html#toc): Provides the framework for creating and executing tests.
2. [pytest-django](https://pytest-django.readthedocs.io/en/latest/): Provides an integration for `pytest` with `Django`.
3. [coverage](https://coverage.readthedocs.io/en/v4.5.x/): Provides the framework for reporting on the project's test coverage and web integrations for viewing the test coverage of the project.

## Best Practices


### Abstraction

With the exception of the data-layer (i.e. the layer responsible for generating
fake data for the tests to use), tests should contain minimal to no abstraction.
We need not get in the habit of writing tests for our tests.

Abstraction can also confuse `pytest`'s ability to output details about the
failed tests and the specific assertion that failed.

##### Example

This is an example of a bad abstraction:

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
identified and fixed when developing an integration that has existing tests.

## pytest

### Running Tests

In order to run tests, your virtual environment must bee activated.

#### Running All Tests

In order to run tests, we need to either be in the root directory.  If in the
root directory, tests can be run as `pytest ./tests`:

```bash
$ cd greenbudget-api
$ pytest ./tests
```

This block will run all of the tests that are written in files
named `tests/test_*.py` or `tests/*_test.py`.  Note, as long as the file is
named `test_*.py` or `*_test.py`, the tests will run.  That means that tests
will be run if they are in a file at `tests/folder/test_*.py`.


#### Running Specific Tests

`pytest` provides the ability to run a specific test or a set of specific tests.

##### Running all tests within a specific file:

```bash
$ pytest tests/test_config.py
```

##### Running a specific test function in a specific file:

```bash
$ pytest tests/test_config.py::test_my_function
```

##### Running a specific test class in a specific file:

```bash
$ pytest tests/test_tests.py::TestClass
```

##### Running a specific test method on a test class in a specific file:

```bash
$ pytest tests/test_tests.py::TestClass::test_my_method
```

### Testing Functionality

#### Assert Exception was Raised

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
specific test fails.  This can be done as follows:


```python
@pytest.mark.xfail
def test_function():
    ...
```


or:


```python
def test_function(condition):
    if condition.is_set:
        pytest.xfail("condition is set")
```


#### Parameterized Test Functions

This allows for decorating test functions with parameterized inputs with a list of
`(input, output)` tuples.

Each iteration over the parameterized inputs counts as a discrete test.

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

### Fixtures

`pytest` uses a concept called [fixtures](https://docs.pytest.org/en/latest/fixture.html)
(not to be confused with Django fixtures, for populating the database from JSON files).
Fixtures are a set of resources that are set up before a test starts and tore down after
the test ends.  They can be thought of as being similiar to `unittest`'s `setupTest` method
on a `unittest.TestCase` class.

Fixtures are stored in files that are named `conftest.py`.  `pytest` will automatically find all
fixtures in these files (as long as the files are in the `tests` directory) and will load the
fixtures to be used before tests are run.

###### tests/conftest.py


```
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

###### tests/test_user.py


```python
def test_resource(my_resource):
    assert my_resource.user.username == 'username'
    assert my_resource.read() == b'Some data'
```

#### Useful Fixtures

`pytest` comes with some fixtures out of the box.  Additionally, `pytest-django`
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

## pytest-django

`pytest-django` is a package that allows `pytest` to seamlessly integrate
with Django.  The package provides many useful fixtures and marks that allow
your tests to interact with the database and other Django core functionality.

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