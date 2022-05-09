# HappyBudget API

&copy; Nick Florin, 2022

This project serves as a REST API supporting the HappyBudget platform.

This documentation outlines how to properly setup and configure the application
in both production and local environments. For other documentation regarding
the operation and development of this project, refer to the following list:

1. [Testing](https://github.com/Saturation-IO/happybudget-api/blob/develop/tests/ReadMe.md)
2. [Standards & Conventions](https://github.com/Saturation-IO/happybudget-api/blob/develop/Standards.md)
3. [Configuration](https://github.com/Saturation-IO/happybudget-api/blob/develop/src/happybudget/conf/ReadMe.md)

### System Requirements

- pyenv
- homebrew
- poetry
- postgres

Note that this documentation describes how to setup/configure the application for
local development on MacOSX. The steps outlined here can be done on a
Windows/Ubuntu machine as well, but the steps will not be exactly as they are
here (for obvious reasons).

## Getting Started

#### Step 1: Repository

Clone this repository locally and `cd` into the directory.

```bash
$ git clone https://github.com/Saturation-IO/happybudget-api.git
```

#### Step 2: Environment

##### Python Version

First, you need to install [`pyenv`](https://github.com/pyenv/pyenv-virtualenv),
a Python version manager for development. This will allow you to manage your
Python version on a project basis.

```bash
$ brew install pyenv
```

We then need to initialize `pyenv`, so add this to your `~/.bash_profile`
(or `~/.zshrc`, or whatever default shell script your machine uses):

```bash
$ eval "$(pyenv init -)"
```

Then source your shell profile as:

```bash
$ . . ~/.bash_profile
```

Get `pyenv` setup with the Python version you will need for this application.

```bash
$ pyenv install 3.9.0
$ pyenv local 3.9.0
```

> Note: If using MacOS 11, certain Python versions do not build (at the time of
> this documentation) and the only versions that have patches for the fix are
> 3.7.8+, 3.8.4+, 3.9.0+. Any earlier versions will not build.

Confirm that `pyenv` is pointing at the correct Python version:

```bash
$ pyenv local
$ 3.9.0
```

If your `pyenv` local Python version is still pointing at your system Python
version, update your `~/.bash_profile` (or `~/.zshrc`, or whatever default shell
script your machine uses) to initialize `pyenv` as follows:

```bash
$ eval "$(pyenv init --path)"
```

Then, resource the shell profile and make sure that `pyenv` is pointing at the
local Python version:

```bash
$ . . ~/.bash_profile
$ pyenv local
$ 3.9.0
```

If this still doesn't work, contact a team member before proceeding further.

##### Dependencies

Now we need to setup the dependencies. We use [`poetry`](https://python-poetry.org/docs/)
as a dependency management system, so you will have to install that locally:

```bash
$ curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

Note that you may need to upgrade `pip` before installing [`poetry`](https://python-poetry.org/docs/),
you can do this as follows:

```bash
$ python -m pip install --upgrade pip
```

Once [`poetry`](https://python-poetry.org/docs/) is intalled, you need to add
it to you `PATH`:

```bash
$ export PATH=$HOME/.poetry/bin:$PATH
```

Now that [`poetry`](https://python-poetry.org/docs/) is installed and on the
system path, you need to create a virtual environment and install the dependencies
to that virtual environment.

```bash
$ python -m venv ./<env_name>
$ . ./<env_name>/bin/activate
$ poetry install
```

Note that [`poetry`](https://python-poetry.org/docs/) has the ability to manage
virtual environments for you, so there is also that option if you do not feel
like managing it yourself.

##### ENV File

Finally, we need to create and edit a `.env` file in the project root to include
configuration values and sensitive information. Ask another team member for help
with this. In order to run the application locally, the `.env` file must specify
the `DJANGO_SECRET_KEY`. The other ENV variables pertain to AWS configuration or
RSA fingerprints for JWT - these should not be needed when running locally.

##### Local Domain

Our authentication protocols rely on the ability to set cookies in the response
that dictate user sessions and user information. Recent Google Chrome security
improvements have introduced the caveat that the browser no longer considers
`localhost` a valid domain, so setting cookies in the backend for the frontend
application no longer works when running the application on `localhost`. For this
reason, the application is configured locally to **only** work on `127.0.0.1:8000`,
not `localhost:8000`. However, the frontend expects that the API will be running
on `local.happybudget.io:8000`, so we need to setup our `/etc/hosts` file such
that we can use `local.happybudget.io` as a valid domain for the local development
server. Note that this step is also included in the frontend setup, so this may
have already been done as a part of that setup but is repeated here for
completeness.

Edit your `/etc/hosts` file as follows:

```bash
$ sudo nano /etc/hosts
```

Add the following configuration to the file:

```bash
127.0.0.1       local.happybudget.io
```

Now, when we start the development server, we will be able to access the backend
application at `local.happybudget.io:8000`, and the frontend application at
`local.happybudget.io:3000`.

##### Local Database

We use `postgresql` for our local (and production) databases, with the exception
being our tests which run on a lightweight `sqlite` database so they can do
transactional tests that do not take forever to run. The first step is to install
`postgres`:

```bash
$ brew install postgres
```

Then, we need to start `postgres` as a service:

```bash
$ brew services start postgresql
```

The database configuration parameters can be overridden in a `.env` file, but
locally they default to the following if not present in the `.env` file:

```bash
DATABASE_NAME=postgres_happybudget
DATABASE_USER=happybudget
DATABASE_PASSWORD=''
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

`postgresql` will, by default, setup a database named `postgres` with `postgres`
as the user. Additionally, `django` will try to (by default) use "django" as the
`DATABASE_USER`. To avoid complications around this, as well as complications
that might arise from a developer already having the default `postgres` database
name reserved for other purposes, we try to isolate these parameters to our use
case.

This is not to say that you cannot use the application on the default `postgresql`
parameters - you can, you just have to set them in the `.env` file.

When starting Django, we may see some of the following database errors:

```bash
$ django.db.utils.OperationalError: connection to server at "localhost" (::1), port 5432 failed: FATAL:
$ database "postgres_happybudget" does not exist
```

This happens if the database has not yet been created. We may also see the
following:

```bash
$ django.db.utils.OperationalError: FATAL:  role "happybudget" does not exist
```

This happens if the database user has not yet been created or does not have the
correct privileges to access the configured database.

Both of these errors mean is that we have to setup the database manually, since
it is not already setup by `postgresql` by default (which it would be, if we were
using the `postgres` database name and user).

To setup the database, we have to follow the steps outlined below. Note that not
all of these steps are required each time, as some of the entities may already
have been created or appropriately assigned when using a previous database or
previously completing some of these steps.

###### Connect to Default Postgres Database

Since we do not know whether or not the database we are concerned with has been
created yet, we connect to the default database `postgres` since we can still
run commands for other databases from that entry point.

```bash
$ psql -d postgres
```

###### Create the Database

If the database was not already created, we need to create it.

```bash
$ CREATE DATABASE <DATABASE_NAME>;
```

###### Create the Database User

If the user does not already exist, we need to create one in Postgres. Note that
if different databases are using the same user, the user may already have been
created.

```bash
$ CREATE USER <DATABASE_USER> WITH PASSWORD '';
```

###### Grant Privileges to Database User

If the database was just created, or the user was just created, we need to grant
access to the created or existing database to the created or existing user.

```bash
$ GRANT ALL PRIVILEGES ON DATABASE <DATABASE_NAME> TO <DATABASE_USER>;
```

###### Assign User as Owner of Database

If the database was just created, or the user was just created, we need to
assign the created or existing user as the owner of the created or existing
database.

```bash
$ ALTER DATABASE <DATABASE_NAME> OWNER TO <DATABASE_USER>;
```

###### Quit the Postgres Shell

```bash
$ \q
```

##### Populating the Database

Now that the application environment is setup, there is some data we need to
populate in the database before we can run the application. This can either be
done via the automated setup command or as outlined here in the explicit steps.

Again, make sure that our virtual environment is activated and that `postgres`
is running.

```bash
$ . ./env/bin/activate
$ brew services start postgresql
```

###### Automated Setup Command

Simply run the following:

```bash
$ python src/manage.py setup
```

This will automatically wipe the local database defined in the `.env` file, run
migrations, install fixtures and prompt you for information to create a
`superuser`. You should always have a `superuser` account locally, and should
use that as your primary account for logging into the application.

###### Explicit Setup Commands

If opting not to use the automated setup command (either due to errors with
it's usage or personal preference),

The first step is only applicable if we are setting up the application after it
was previously setup and a database was created. If we want to start from
scratch, we can wipe the database defined in the `.env` file as follows:

```bash
$ python src/manage.py reset_db
```

If setting up for the first time, or setting up with an existing database, this
step can be ignored.

Next, we need to run migrations such that the database tables and schemas are
populated in the database. To do this, simply run the following command:

```bash
$ python src/manage.py migrate
```

Next, we need to load the fixtures into the database:

```bash
$ python src/manage.py loadfixtures
```

Then, we need to collect the server side static files for the admin:

```bash
$ python src/manage.py collectstatic
```

Finally, we need to create a superuser that we will use to login to the
application with:

```bash
$ python src/manage.py createsuperuser
```

You should always have a `superuser` account locally, and should use that as
your primary account for logging into the application.

Congratulations! You are now ready to run the application.

## Development

### Workflow

Developers should be free to use whatever workflow works best for them, and the
IDE they use is an important aspect of that workflow.

#### IDE

While it is not required that a developer use
[VSCode](https://code.visualstudio.com/), it is strongly, strongly recommended
that they do. Usage of [VSCode](https://code.visualstudio.com/) will mean that
the setup for the team's code environment will more seamlessly integrate into
your workflow.

If [VSCode](https://code.visualstudio.com/) is not the ideal IDE for you, that
is fine - but it is your responsibility to make sure that the IDE of your
choosing is properly setup for the team's code environment, which primary relates
to (but is not limited to) linting.

##### Extensions

If using [VSCode](https://code.visualstudio.com/), please make sure to
install the `"ms-python.vscode-pylance"` and `"ms-python.python"` extensions
from the [VSCode](https://code.visualstudio.com/) marketplace.

##### `settings.json`

For [VSCode](https://code.visualstudio.com/) to function properly with the
code environment configuration remote to this repository, you should add the
following configurations to your `settings.json` file:

```json
{
  "editor.formatOnSave": true,
  "[python]": {
    "editor.tabSize": 4,
    "editor.insertSpaces": true,
    "editor.formatOnSave": true
  },
  "python.linting.flake8Enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8CategorySeverity.W": "Error",
  "python.linting.pycodestyleEnabled": true,
  "editor.rulers": [80, 100],
  "python.languageServer": "Pylance"
}
```

### Running Locally

To run the application locally, simply activate the virtual environment and
start the Django web server:

```bash
$ . ./env/bin/activate
$ python src/manage.py runserver
```

#### Django Settings

By default, the Django settings module used when running locally (toggled via
the `DJANGO_SETTINGS_MODULE` environment variable) is `happybudget.conf.settings.local`.
If you need to override certain settings for your own personal local development,
`happybudget.conf.settings.local` should not be edited but instead a
`happybudget.conf.settings.local_override` Python file should be created.

### Testing

See the `ReadMe.md` file in the `testing` directory
[here](https://github.com/Saturation-IO/happybudget-api/blob/develop/tests/ReadMe.md).

#### tox

We use `tox` to automate our testing, linting and code coverage processes.
`tox` was a project that began as a way to run tests across Python versions,
Django versions and other package versions - but has extended itself to much
more.

Our `tox` setup can be very useful for local development. One benefit of `tox`
is that it completely isolates it's own cached virtual environments for purposes
of running tests and producing coverage reports. The following commands can all
be run outside of a virtual environment:

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

Running these commands will usually be slow the first time, just because `tox`
has to setup the cached environment - but after that, they all run very quickly
and can be very useful.

### Managing Dependencies

We use [`poetry`](https://python-poetry.org/docs/) as a package management system.
[`poetry`](https://python-poetry.org/docs/)'s analogue to a `requirements.txt`
file is the `pyproject.toml` file. Whenever you need to add or remove dependencies
from the project, the `pyproject.toml` file will be updated to reflect the new
dependency state.

See the discussion in **Getting Started** for instructions on how to install
and setup [`poetry`](https://python-poetry.org/docs/).

#### Installing All Packages

The [`poetry`](https://python-poetry.org/docs/) analogue to
`pip install -r requirements.txt` is as follows:

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

## Application Environments

| Environment |          Settings Module          |             URL             |      File Storage      |          Database          |
| :---------: | :-------------------------------: | :-------------------------: | :--------------------: | :------------------------: |
|   `local`   | `happybudget.conf.settings.local` | `local.happybudget.io:8000` |   Local File Storage   |  Local PostgreSQL Server   |
|   `test`    | `happybudget.conf.settings.test`  |             N/A             | Temporary File Storage | Transactional SQLite3 File |
|  `develop`  |  `happybudget.conf.settings.dev`  |   `devapi.happybudget.io`   |         AWS S3         |   PostgreSQL on AWS RDS    |
|   `prod`    | `happybudget.conf.settings.prod`  |    `api.happybudget.io`     |         AWS S3         |   PostgreSQL on AWS RDS    |

## Setting Up on EC2 Instance

The setup instructions in this section describe the steps required to setup and
run the API on a Linux EC2 AWS instance. If a machine other than Linux is chosen,
these steps will differ.

These instructions do not detail how to setup the EC2 instance in AWS, but rather
detail how to setup the API on an EC2 instance assuming it has already been
created.

Currently, we run EC2 instances for two separate environments:

| Environment |         Settings Module          |           URL           |
| :---------: | :------------------------------: | :---------------------: |
|  `develop`  | `happybudget.conf.settings.dev`  | `devapi.happybudget.io` |
|   `prod`    | `happybudget.conf.settings.prod` |  `api.happybudget.io`   |

#### Step 1: Installing Git

After SSH'ing into the EC2 instance, we first need to install `git` on the machine.
To install `git` on the EC2 instance, simply run:

```bash
$ sudo yum update
$ sudo yum install git -y
```

We then need to create the SSH keys for `git` that will authenticate the machine
for SSH requests to `git`.

```bash
$ ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

A passphrase is not required for the SSH key, and the key should be saved in
it's default location which is usually `~/.ssh/id_rsa`.

We then need to modify the SSH configuration to automatically include this SSH
key. To do this, edit the `~/.ssh/config` file as follows:

```bash
$ sudo nano ~/.ssh/config
```

```
Host *
  AddKeysToAgent yes
  IdentityFile ~/.ssh/id_rsa
```

This assumes that your SSH key was created in `~/.ssh/id_rsa`.

Finally, we just need to start the `ssh-agent` in the background and add the
newly created identity:

```bash
$ eval "$(ssh-agent -s)"
$ ssh-add ~/.ssh/id_rsa
```

In order for `git` to allow SSH access to the machine, we now need to add that
SSH key to `git`. To do this, login to your GitHub account (or an organization
GitHub account that has access to the repository) and go to the Settings page.
Under "SSH and GPG Keys", click "Add SSH Key". Read the public key content on
the machine and copy and paste it into the GitHub field:

```bash
tail ~/.ssh/id_rsa.pub
```

#### Step 2: Installing Docker

We now need to install `docker` and `docker-compose` on the machine. To install
`docker`, run the following command:

```bash
$ sudo amazon-linux-extras install docker
```

Once `docker` is installed, we need to start the `docker` service and add the
`ec2-user` to the `docker` group so we can execute `docker` commands without
using `sudo`:

```bash
$ sudo service docker start
$ sudo usermod -a -G docker ec2-user
```

Logout from the EC2 instance and then SSH back in. Verify that you can run
`docker` commands without `sudo`:

```bash
$ docker info
```

Finally, we simply need to install `docker-compose`:

```bash
$ sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Step 3: Clone Repository

After SSH'ing into the instance, we need to clone the `git` repository. Make a
top level directory `www` with the correct permissions and clone the repository
into that directory:

```bash
$ sudo mkdir www
$ sudo chmod 777 www
$ chmod go-w ~/.ssh/config
$ cd ./www
$ git clone git@github.com:Saturation-IO/happybudget-api.git
$ cd ./happybudget-api
```

##### ENV File

We need to create a `.env` file to hold the sensitive keys required to run the
API. You should talk to a team member to get these key values before proceeding.
The `.env` file should look as follows:

```
DJANGO_SECRET_KEY=<DJANGO_SECRET_KEY>
DJANGO_SETTINGS_MODULE=<DJANGO_SETTINGS_MODULE>

DATABASE_NAME=<RDS_DATABASE_NAME>
DATABASE_USER=<RDS_DATABASE_USER>
DATABASE_PASSWORD=<RDS_DATABASE_PASSWORD>
DATABASE_HOST=<RDS_DATABASE_HOST>
DATABASE_PORT=5432

AWS_STORAGE_BUCKET_NAME=<AWS_STORAGE_BUCKET_NAME>
AWS_STORAGE_BUCKET_URL=<AWS_STORAGE_BUCKET_URL>
AWS_S3_REGION_NAME=<AWS_S3_REGION_NAME>
AWS_SECRET_ACCESS_KEY=<AWS_SECRET_ACCESS_KEY >
AWS_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID>

JWT_RSA_FINGERPRINT=<JWT_RSA_FINGERPRINT>
```

Note that `DJANGO_SETTINGS_MODULE` will be set based on the environment of the
EC2 instance.

###### JWT RSA Signing Fingerprint

This step is very important. To dramatically improve the security of the
application, we do not use the `DJANGO_SECRET_KEY` to sign JWT tokens used
throughout the application. Instead, we use an RSA fingerprint, because it is
significantly more secure and is easier to swap out if it ever becomes compromised.

In local and test environments, the RSA fingerprint defaults to a value that does
not need to be stored sensitively. However, in production and development
environments, we need to generate the RSA public/private key pairs on the server
so they can be securely stored and referenced by the application.

To start, generate a private/public RSA key pair as follows:

```bash
$ ssh-keygen -m PEM -t rsa -b 4096 -C "your_email@example.com"
```

You will then be prompted to enter the file for which the key should be saved.
Since we will be reading the file contents in the application itself, the
private/public key pairs need to be stored inside of the `docker` environment.
Our `docker` setup expects the file to be named `jwt_signing_key`, and in order
for it to be copied to the `docker` environment, and found by Django, it needs
to be stored in the `BASE_DIR`:

```bash
$ Enter file in which to save the key (/home/ec2-user/.ssh/id_rsa): /www/happybudget-api/src/happybudget/jwt_signing_key
```

Do not enter a passphrase.

**Important**: Do not ever, under any circumstances, remove this file from the
EC2 instance, commit to source control or share with another person, inside or
outside of the company.

Now that we have the private/public RSA key pairs generated, we simply need to
reference it's filename in the `.env` file, since Django will by default try to
find it in `src/happybudget/<filename>`. The RSA private/public key pairs are in
the root of the `docker` environment, so this is simply:

```bash
$ nano .env
$ JWT_RSA_FINGERPRINT_FILENAME=jwt_signing_key
```

The application will now automatically read both the file and it's `.pub`
counterpart and use the file contents to sign the JWT tokens in the application.

#### Step 4: Configuring Apache

On the EC2 instance, we need to use Apache as a proxy to route requests on port
`80` to requests on port `8000` where the application is running. Requests are
mapped to port `80` via the load balancer in AWS, which will route requests on
port `443` (for HTTPS) to port `80`.

First, we need to install `httpd`:

```bash
$ sudo yum install httpd
```

Next, we just need to edit the Apache configuration to route requests as
described above:

```bash
$ cd /etc/httpd
$ touch vhosts.conf
$ sudo nano vhosts.conf
```

Add the following content to `vhosts.conf`:

```
<VirtualHost *:80>
  ProxyPreserveHost On
  ProxyRequests Off
  ServerName viska.localhost
  ProxyPass / http://localhost:8000/
  ProxyPassReverse / http://localhost:8000/

  Timeout 3600
  ProxyTimeout 3600
  ProxyBadHeader Ignore

  ErrorLog "/var/log/httpd/gb-error_log"
  CustomLog "/var/log/httpd/gb-access_log" common

</VirtualHost>
```

Finally, run the `httpd` service in the background:

```
$ sudo service httpd start
```

#### Step 5: Running the Application

When running the application, the `docker-compose` configuration file we use
depends on the environment. In the `prod` environment, the configuration file is
simply `docker-compose.yml` - which is the default. However, in the `dev`
environment, we need to specify the configuration file as `docker-compose.dev.yml`.
For this reason, the directions to start the application in each environment
differ slightly.

##### Prod Environment

Check your `.env` file and make sure that
`DJANGO_SETTINGS_MODULE=happybudget.conf.settings.prod`. Then, check out the
`master` branch:

```bash
$ git fetch origin master
$ git checkout master
$ git pull
```

Then, we simply need to build the container and bring it up and then run `Django`
management commands _when applicable_.

```bash
$ docker-compose up -d --build
$ docker-compose exec web python manage.py migrate
$ docker-compose exec web python manage.py collectstatic
$ docker-compose exec web python manage.py loadfixtures
$ docker-compose exec web python manage.py createsuperuser
```

##### Dev Environment

Check your `.env` file and make sure that
`DJANGO_SETTINGS_MODULE=happybudget.conf.settings.dev`. Then, check out the
`develop` branch:

```bash
$ git fetch origin develop
$ git checkout develop
$ git pull
```

Then, we simply need to build the container and bring it up and then run
`Django` management commands _when applicable_.

```bash
$ docker-compose -f docker-compose.dev.yml up -d --build
$ docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
$ docker-compose -f docker-compose.dev.yml exec web python manage.py collectstatic
$ docker-compose -f docker-compose.dev.yml exec web python manage.py loadfixtures
$ docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```
