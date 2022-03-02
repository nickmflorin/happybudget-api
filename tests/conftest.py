import logging
import pytest

from django.conf import settings
from django.db import connections

from pytest_django.fixtures import _disable_native_migrations

from .factories import *  # noqa
from .http import *  # noqa
from .models import *  # noqa
from .static import *  # noqa
from .stripe import *  # noqa


def pytest_addoption(parser):
    parser.addoption(
        "--postgresdb",
        action="store_true",
        help="Run tests that require a postgres database.",
    )


def pytest_runtest_setup(item):
    """
    Instructs the testing suite to skip a test if tests are being run with the
    `--postgresdb` flag and the test is not marked with
    `@pytest.mark.postgresdb`.  Conversely, instructs the testing suite to skip
    a test if the test is marked with `@pytest.mark.postgresdb` and the tests
    are not being run with the `--postgresdb` flag.

    Note:
    ----
    This is a hook that is automatically recognized and called by pytest before
    each individual test runs.  Changing it's name will cause it not to be
    recognized.
    """
    postgres_db_flagged = item.config.getoption("--postgresdb")
    postgres_marks = [mark for mark in item.iter_markers(name="postgresdb")]
    need_to_write_marks = [
        mark for mark in item.iter_markers(name="needdtowrite")]
    if need_to_write_marks:
        pytest.skip(f"Test {item.original_name} needs to be written.")
    elif postgres_marks and not postgres_db_flagged:
        pytest.skip("Test requires postgres database.")
    elif postgres_db_flagged and not postgres_marks:
        pytest.skip("Test only runs on postgres database.")


@pytest.fixture(scope='session')
def django_db_setup(
    request,
    django_test_environment: None,
    django_db_blocker,
    django_db_use_migrations: bool,
    django_db_keepdb: bool,
    django_db_createdb: bool,
    django_db_modify_db_settings: None,
    pytestconfig
) -> None:
    """
    Top-level fixture called by `pytest_django` that prepares the test databases
    for use before the tests begin.

    We only want to override the default behavior of this fixture in the case
    that the tests are run with the `--postgresdb` flag, in which case we want
    to dynamically swap out the sqlite database for a postgres database.

    Note:
    ----
    Unforunately, since the original
    :obj:`pytest_django.fixtures.django_db_setup` method is a pytest fixture,
    we cannot call it directly - which means we have to reimplement the entire
    thing, just injecting our custom logic where applicable.

    Note:
    ----
    The tear down logic here, in the Postgres case, does not seem to be actually
    removing the test database entirely.  This has not been problematic however,
    as data isn't actually persisting to the test database in the tests (due to
    internal mechanics of Django).

    We may want to investigate why the database is not deleting and/or make it
    such that the `--postgresdb` flag implies that the database should be kept
    between tests (`--keepdb` flag).
    """
    from django.test.utils import setup_databases, teardown_databases

    def before_postgres_db_setup():
        """
        Triggers Django's connections manager to reprovision the database
        connection using the altered settings in this fixture.

        At the time that this fixture is called, Django will have already
        established the database connection and configured the connection
        objects with the settings defined in `greenbudget.conf.settings.test`
        before we have a chance to alter the database configuration here. This
        means that after we alter the database configuration here, we must
        reestablish those related connections so the database setup and teardown
        methods function properly.
        """
        connections["default"] = connections.create_connection("default")

    # If the tests are being run with the `--postgresdb` flag, we want to swap
    # out the default `sqlite` database in settings for the test Postgres DB.
    postgresdb = pytestconfig.getoption('postgresdb')
    if postgresdb:
        if not hasattr(settings, 'TEST_POSTGRES_DB'):
            raise Exception("Postgres database not configured in settings.")

        # Set the test Postgres database as the default database.
        settings.DATABASES["default"] = settings.TEST_POSTGRES_DB

        # By default, Django will prefix our test database with "test_" which
        # makes things very confusing.  To avoid this, we define the `TEST`
        # sub-dictionary and explicitly set the test database name.
        settings.DATABASES["default"].update(TEST={
            "NAME": settings.TEST_POSTGRES_DB["NAME"]
        })

    # The logic below is implemented exactly the same way as the default
    # `pytest_django.fixtures.django_db_setup` fixture, except for the 1
    # conditional block that reprovisions the connections in the case that the
    # database settings changed when running tests with the `--postgresdb` flag.
    setup_databases_args = {}

    if not django_db_use_migrations:
        _disable_native_migrations()

    if django_db_keepdb and not django_db_createdb:
        setup_databases_args["keepdb"] = True

    with django_db_blocker.unblock():
        # Reprovision database connections based on the altered database settings
        # when running tests with the `--postgresdb` flag.
        if postgresdb:
            before_postgres_db_setup()

        db_cfg = setup_databases(
            verbosity=request.config.option.verbose,
            interactive=False,
            **setup_databases_args
        )

        # Run the actual test.
        yield

        def teardown_database() -> None:
            with django_db_blocker.unblock():
                try:
                    teardown_databases(
                        db_cfg, verbosity=request.config.option.verbose)
                except Exception as exc:
                    request.node.warn(
                        pytest.PytestWarning(
                            "Error when trying to teardown test databases: %r"
                            % exc
                        )
                    )
        if not django_db_keepdb:
            request.addfinalizer(teardown_database)


@pytest.fixture(autouse=True)
def disable_logging(caplog):
    """
    Disable logging behavior in certain packages.
    """
    caplog.set_level(logging.CRITICAL, logger="factory")
    caplog.set_level(logging.CRITICAL, logger="faker.factory")
    caplog.set_level(logging.CRITICAL, logger="factory-boy")
    caplog.set_level(logging.INFO, logger="greenbudget")
