# Green Budget API

### System Requirements

- pyenv
- homebrew
- poetry
- postgres

Note that this documentation describes how to setup/configure the application for local development
on MacOSX.  The steps outlined here can be done on a Windows/Ubuntu machine as well, but the steps
will not be exactly as they are here (for obvious reasons).

## Getting Started

#### Step 1: Repository

Clone this repository locally and `cd` into the directory.

```bash
$ git clone https://github.com/Saturation-IO/greenbudget-api.git
```

#### Step 2: Environment

##### Python Version

Install [`pyenv`](https://github.com/pyenv/pyenv-virtualenv) first. This will
allow you to manage your Python version on a project basis.

```bash
$ brew install pyenv
```

Get `pyenv` setup with the Python version you will need for this application.

```bash
$ pyenv install 3.8.2
$ pyenv local 3.8.2
```

Confirm that `pyenv` is pointing at the correct Python version:

```bash
$ pyenv local
$ 3.8.2
```

##### Dependencies

Now we need to setup the dependencies. We use [`poetry`](https://python-poetry.org/docs/)
as a dependency management system, so you will have to install that locally:

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

Then, you need to add it to you `PATH`:

```bash
export PATH=$HOME/.poetry/bin:$PATH
```

Now that [`poetry`](https://python-poetry.org/docs/) is setup, you need to create a virtual environment and install
the dependencies to that virtual environment.

```bash
$ python -m <env_name> ./<env_name>
$ pyenv virtualenv 3.8.2 <env_name>
$ . ./<env_name>/bin/activate
$ poetry install
```

Note that [`poetry`](https://python-poetry.org/docs/) has the ability to manage virtual environments for you, so
there is also that option if you do not feel like managing it yourself.

##### ENV File

Finally, we need to create and edit a `.env` file in the project root to include configuration values and
sensitive information. Ask another team member for help with this.  In order to run the application locally,
the `.env` file must specify the `DJANGO_SECRET_KEY`.  The other ENV variables pertain to AWS configuration that
should not be needed when running locally.

## Running Locally

To run the application locally, simply activate the virtual environment, start postgres app, and start the Django web server:

```bash
$ . ./env/bin/activate
$ python src/manage.py runserver
```

Then, migrate to the domain/port serving the Frontend (assuming that the Frontend server is running, this
is usually at `127.0.0.1:3000`.

#### Local Database

We use `postgresql` for our local (and production) databases, with the exception being our tests which run on
a lightweight `sqlite` database so they can do transactional tests that do not take forever to run.

The database configuration parameters can be overridden in a `.env` file, but locally they default to the following
if not present in the `.env` file:

```bash
DATABASE_NAME=postgres_greenbudget
DATABASE_USER=greenbudget
DATABASE_PASSWORD=''
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

`postgresql` will, by default, setup a database named `postgres` with `postgres` as the user.  Additionally, `django`
will try to (by default) use `django` as the `DATABASE_USER`.  To avoid complications around this, as well as complications
that might arise from a developer already having the default `postgres` database name reserved for other purposes, we try to
isolate these parameters to our use case.

This is not to say that you cannot use the application on the default `postgresql` parameters - you can, you just have to set
them in the `.env` file.

For developers not familiar with `postgresql`, because we do not use the default `postgresql` parameters, you might see the following
error when starting the server locally:

```bash
django.db.utils.OperationalError: FATAL:  role "greenbudget" does not exist
```

All this means is that we have to setup the database manually, since it is not already setup by `postgresql` by default (which
it would be, if we were using the `postgres` database name and user).

To setup the database, all we have to do is the following:

```bash
psql -d postgres  # Open the postgresql shell by connecting to the default database.
CREATE DATABASE postgres_greenbudget;
CREATE USER greenbudget WITH PASSWORD '';
GRANT ALL PRIVILEGES ON DATABASE postgres_greenbudget TO greenbudget;
ALTER USER greenbudget CREATEDB;
ALTER DATABASE postgres_greenbudget OWNER TO greenbudget;
\q
```

#### Local Domain Caveat

Our authentication protocols rely on the ability to set cookies in the response that dictate user sessions and
information.  Recent Google Chrome security improvements have introduced the caveat that the browser no longer
considers `localhost` a valid domain, so setting cookies in the backend for the frontend application no longer
works when running the application on `localhost`.  For this reason, the application is configured locally to
**only** work on `127.0.0.1:8000`, not `localhost:8000`.

#### Django Settings

By default, the Django settings module used when running locally (toggled via the `DJANGO_SETTINGS_MODULE` environment
variable) is `greenbudget.conf.settings.local`.  If you need to override certain settings for your own personal
local development, `greenbudget.conf.settings.local` should not be edited but instead a `greenbudget.conf.settings.local_override`
Python file should be created.

##### Local Override Use Case

A common use case for overriding the local settings configuration might be to run the application using an `sqlite`
database (not the default `postgresql` database).  To do this, create `greenbudget.conf.settings.local` as
follows:

```python
import dj_database_url
from .base import BASE_DIR

DATABASES = {
    'default': dj_database_url.parse('sqlite:///%s/db.sqlite3' % BASE_DIR)  # noqa
}
```

When `greenbudget.conf.settings.local` is loaded, it will look for a `local_override` file in the same
directory, and if it exists, will import the settings configurations in that file after the configurations
in the local file are loaded.


## Testing

See the ReadMe in `testing/ReadMe.md`.

#### tox

We use `tox` to automate our testing, linting and code coverage processes.  `tox` was a project that began
as a way to run tests across Python versions, Django versions and other package versions - but has extended
itself to much more.

Our `tox` setup can be very useful for local development.  One benefit of `tox` is that it completely isolates
it's own cached virtual environments for purposes of running tests and producing coverage reports.  The following
commands can all be run outside of a virtual environment:

Run the complete `pytest` suite and generate coverage reports in `/reports`:

```bash
$ tox
```

or

```bash
tox -e test
```

Clean all build and test directories as well as extraneous artifacts:

```bash
tox -e clean
```

Run `flake8` linting checks and generate linting reports in `/reports`:

```bash
tox -e lint
```

Running these commands will usually be slow the first time, just because `tox` has to setup the cached
environment - but after that, they all run very quickly and can be very useful.

## Managing Dependencies

We use [`poetry`](https://python-poetry.org/docs/) as a package management system.
[`poetry`](https://python-poetry.org/docs/)'s analogue to a `requirements.txt`
file is the `pyproject.toml` file. Whenever you need to add or remove dependencies
from the project, the `pyproject.toml` file will be updated to reflect the new
dependency state.

See the discussion in **Getting Started** for instructions on how to install
and setup [`poetry`](https://python-poetry.org/docs/).

#### Installing All Packages

The [`poetry`](https://python-poetry.org/docs/) analogue to `pip install -r requirements.txt` is as follows:

```bash
$ poetry install
```

This will install/update all of the packages in the `pyproject.toml` file.

#### Installing a Specific Package

To install a specific package with [`poetry`](https://python-poetry.org/docs/),
all you have to do is:

```bash
$ poetry add <package-name>
```

This will install the package in your virtual environment and update the
`pyproject.toml` file.

#### Remove a Specific Package

To remove a specific package with [`poetry`](https://python-poetry.org/docs/),
all you have to do is:

```bash
$ poetry remove <package-name>
```

This will remove the package from your virtual environment and update the
`pyproject.toml` file.

#### Development vs. Production Dependencies

[`poetry`](https://python-poetry.org/docs/) uses a concept of development
dependencies to allow additional dependencies to be included for local development
that we do not want to add in a production environment. By default, when
running `poetry install` it will include the development dependencies. In production,
we use `poetry install --no-dev` so that development dependencies are not included.
