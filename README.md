# Green Budget API

### System Requirements

- Docker
- pyenv
- homebrew
- MacOSX (Docker is still rocky on a Windows machine but it can be done).
- poetry

## Getting Started

#### Step 1: Repository

Clone this repository locally and `cd` into the directory.

```bash
$ git clone git clone https://<user>@bitbucket.org/Saturation-IO/greenbudget-api.git.git
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
$ pyenv virtualenv 3.8.2 <env_name>
$ . ./<env_name>/bin/activate
$ poetry install
```

Note that [`poetry`](https://python-poetry.org/docs/) has the ability to manage virtual environments for you, so
there is also that option if you do not feel like managing it yourself.

##### Docker Environment

Now, we need to configure our `docker-compose` environment. Copy the `docker-compose.override-options.yml`
file to `docker-compose.override.yml` in the project root.

```bash
$ cp docker-compose.override-options.yml docker-compose.override.yml
```

Then, edit `docker-compose.override.yml` to make sure all services are active (`celery`, `celery-beat`, ...).

##### ENV File

Finally, we need to create and edit a `.env` file in the project root to include configuration values and
sensitive information. Ask another team member for help with this.  In order to run the application locally,
the `.env` file must specify the `DJANGO_SECRET_KEY`.

## Running Locally

Right now, there are two primary services required to operate the application: `db` and `web`.  Each of these
can be run separately, inside or outside of a `docker` container.  Inside of the container, the `db` service
will run as a `PostgreSQL` server and the `web` service will run via a `gunicorn` web server.  Outside of the
container, the `db` service will be run as a simple `sqlite3` file and the `web` service will be run via a simple
`Django` web server.

#### All Services Inside Container

The simplest way to get the application running locally is to bring up both services inside the `docker` container:

```bash
$ docker-compose up
```

This will bring up both the `db` service and the `web` service.  However, this is usually not the most productive way
to develop locally, since the `web` service will not change when code changes are made.

#### `db` Service Inside Container, `web` Service Outside Container

In order to improve the local development process, we can run the `db` service inside the `docker` container
while using the `Django` web server to run the `web` service.  We can do this as follows:

```bash
$ docker-compose up -d db
$ . ./env/bin/activate
$ python src/manage.py runserver
```

#### Both Services Outside the Container

If we wish to use a lighter weight `sqlite` option for the application database, we can do so as well.  In order
to do these, we need to create a `local.py` file in `src/conf/settings/local.py`.  When we create a `local.py` file,
any settings specified in the file will override those in the `src/config/settings/dev.py` file.  The file should look
something like this:

```python
import dj_database_url
from .dev import *

DATABASES = {
    'default': dj_database_url.parse('sqlite:///%s/db.sqlite3' % BASE_DIR)  # noqa
}
```

Then, we need to set the `DJANGO_SETTINGS_MODULE` environment variable to point to this settings file:

```bash
$ export DJANGO_SETTINGS_MODULE=greenbudget.conf.settings.local.py
```

Now, we can just run the `Django` web server and it will use the local `sqlite` file as it's database:

```bash
$ . ./env/bin/activate
$ python src/manage.py runserver
```

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
