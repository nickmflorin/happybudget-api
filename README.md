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

## Setting Up on EC2 Instance

The setup instructions in this section describe the steps required to setup and run the
API on a Linux EC2 AWS instance.  If a machine other than Linux is chosen, these steps
will differ.

These instructions do not detail how to setup the EC2 instance in AWS, but rather detail
how to setup the API on an EC2 instance assuming it has already been creeated.

Currently, we run EC2 instances for two separate environments:

(1) `develop`: URL = `devapi.greenbudget.io`, `DJANGO_SETTINGS_MODULE` = `greenbudget.conf.settings.dev`
(2) `prod`: URL = `api.greenbudget.io`, `DJANGO_SETTINGS_MODULE` = `greenbudget.conf.settings.prod`

#### Step 1: Installing Git

After SSH'ing into the EC2 instance, we first need to install `git` on the machine. To install `git`
on the EC2 instance, simply run:

```bash
$ sudo yum update
$ sudo yum install git -y
```

We then need to create the SSH keys for `git` that will authenticate the machine for SSH requests
to `git`.

```bash
$ ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

A passphrase is not required for the SSH key, and the key should be saved in it's default location
which is usually `~/.ssh/id_rsa`.

We then need to modify the SSH configuration to automatically include this SSH key.  To do this,
edit the `~/.ssh/config` file as follows:

```bash
$ sudo nano ~/.ssh/config
```

```
Host *
  AddKeysToAgent yes
  IdentityFile ~/.ssh/id_rsa
```

This assumes that your SSH key was created in `~/.ssh/id_rsa`.

Finally, we just need to start the `ssh-agent` in the background and add the newly created identity:

```bash
$ eval "$(ssh-agent -s)"
$ ssh-add ~/.ssh/id_rsa
```

In order for `git` to allow SSH access to the machine, we now need to add that SSH key to `git`.  To do this,
login to your GitHub account (or an organization GitHub account that has access to the repository) and go to
the Settings page.  Under "SSH and GPG Keys", click "Add SSH Key".  Read the public key content on the machine
and copy and paste it into the GitHub field:

```bash
tail ~/.ssh/id_rsa.pub
```

#### Step 2: Installing Docker

We now need to install `docker` and `docker-compose` on the machine.  To install `docker`, run the following
command:

```bash
$ sudo amazon-linux-extras install docker
```

Once `docker` is installed, we need to start the `docker` service and add the `ec2-user` to the `docker` group
so we can execute `docker` commands without using `sudo`:

```bash
$ sudo service docker start
$ sudo usermod -a -G docker ec2-user
```

Logout from the EC2 instance and then SSH back in.  Verify that you can run `docker` commands without `sudo`:

```bash
$ docker info
```

Finally, we simply need to install `docker-compose`:

```bash
$ sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Step 3: Clone Repository

After SSH'ing into the instance, we need to clone the `git` repository.  Make a top level directory `www` with the correct permissions
and clone the repository into that directory:

```bash
$ sudo mkdir www
$ sudo chmod 777 www
$ chmod go-w ~/.ssh/config
$ cd ./www
$ git clone git@github.com:Saturation-IO/greenbudget-api.git
$ cd ./greenbudget-api
```

##### ENV File

We need to create a `.env` file to hold the sensitive keys required to run the API.  You should talk to a team member to get
these key values before proceeding.  The `.env` file should look as follows:

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

JWT_SIGNING_KEY=<JWT_SIGNING_KEY>
JWT_VERIFYING_KEY=<JWT_VERIFYING_KEY>
```

Note that `DJANGO_SETTINGS_MODULE` will be set based on the environment of the EC2 instance.

###### JWT RSA Signing Fingerprint

This step is very important.  To dramatically improve the security of the application, we do not sign the

```bash
$ ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

Enter file in which to save the key (/home/ec2-user/.ssh/id_rsa): /home/ec2-user/.ssh/id_rsa_django

We need to copy both the private and public fingerprints into the `.env` file.  First, read the
private key file:

```bash
$ tail -f 1000 ~/.ssh/id_rsa_django
```

Copy everything between `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----` and
copy into the `.env` file under `JWT_SIGNING_KEY`, using `""` at the beginning and the end of the
key to allow the `.env` file to recognize it as a multi-line variable.

Similiarly, for the public key, read the public key file:

```bash
$ tail -f 1000 ~/.ssh/id_rsa_django.pub
```

Copy everything after `ssh-rsa` and before the email address at the end of the key (the last two characters
of the key should be `==`).  Copy the value into the `.env` file under `JWT_VERIFYING_KEY`, again, using `""`
to denote the multi-line variable in the `.env` file.

#### Step 4: Configuring Apache

On the EC2 instance, we need to use Apache as a proxy to route requests on port `80` to requests
on port `8000` where the application is running.  Requests are mapped to port `80` via the load balancer
in AWS, which will route requests on port `443` (for HTTPS) to port `80`.

First, we need to install `httpd`:

```bash
$ sudo yum install httpd
```

Next, we just need to edit the Apache configuration to route requests as described above:

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

When running the application, the `docker-compose` configuration file we use depends on the environment.  In the
`prod` environment, the configuration file is simply `docker-compose.yml` - which is the default.  However, in
the `dev` environment, we need to specify the configuration file as `docker-compose.dev.yml`.  For this reason, the
directions to start the application in each environment differ slightly.

##### Prod Environment

Check your `.env` file and make sure that `DJANGO_SETTINGS_MODULE=greenbudget.conf.settings.prod`.  Then, check out the
`master` branch:

```bash
$ git fetch origin master
$ git checkout master
$ git pull
```

Then, we simply need to build the container and bring it up and then run `Django` management commands _when applicable_.

```bash
$ docker-compose up -d --build
$ docker-compose exec web python manage.py migrate
$ docker-compose exec web python manage.py collectstatic
$ docker-compose exec web python manage.py loadfixtures
$ docker-compose exec web python manage.py createsuperuser
```

##### Dev Environment

Check your `.env` file and make sure that `DJANGO_SETTINGS_MODULE=greenbudget.conf.settings.dev`.  Then, check out the
`develop` branch:

```bash
$ git fetch origin develop
$ git checkout develop
$ git pull
```

Then, we simply need to build the container and bring it up and then run `Django` management commands _when applicable_.

```bash
$ docker-compose -f docker-compose.dev.yml up -d --build
$ docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
$ docker-compose -f docker-compose.dev.yml exec web python manage.py collectstatic
$ docker-compose -f docker-compose.dev.yml exec web python manage.py loadfixtures
$ docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```
