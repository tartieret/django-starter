# Setup development environment for A320 Quiz project

This project has been generated using django-cookiecutter. Full documentation is available at [https://cookiecutter-django.readthedocs.io/en/latest/index.html](https://cookiecutter-django.readthedocs.io/en/latest/index.html)

## Setup your code editor

In Visual Studio Code, open the control panel (CTRL+P) and enter the following command:
```
ext install EditorConfig.EditorConfig
```
This will install the [EditorConfig](https://marketplace.visualstudio.com/items?itemName=EditorConfig.EditorConfig) extension. From there, the styling configuration for the project is defined in .editorconfig

## Setup python and dependencies

### Automatic install

Enter:
```
make install
```
This creates a virtual environment called .venv and install all the dependencies.

### Manual install

Alternatively, you can process manually step by step by creating a virtual environment using python 3.8
```
python3.8 -m venv .venv
```
Activate the environment and install the dependencies
```
source .venv/bin/activate
```
Install the python packages
```
pip install -r requirements/local.txt
```

## Setup PostgreSQL database


### Install PostgreSQL 11

Follow the installation instructions available here: https://www.postgresql.org/download/linux/ubuntu/

```
sudo apt-get install postgresql postgresql-contrib
```

Open the psql utility with:
```
sudo -u postgres psql
```
You can now control the Postgresql server.

First, create a database for your project:

```Postgres
CREATE DATABASE logbook;
```

**Note:** Every Postgres statement must end with a semi-colon, so make sure that your command ends with one if you are experiencing issues.

Next, create a database user for our project. Make sure to select a secure password:

```Postgres
CREATE USER sqladmin WITH PASSWORD 'cholet49300';
```

Afterwards, we’ll modify a few of the connection parameters for the user we just created. This will speed up database operations so that the correct values do not have to be queried and set each time a connection is established.

We are setting the default encoding to UTF-8, which Django expects. We are also setting the default transaction isolation scheme to “read committed”, which blocks reads from uncommitted transactions. Lastly, we are setting the timezone. By default, our Django projects will be set to use UTC. These are all recommendations from the Django project itself:

```Postgres
ALTER ROLE sqladmin SET client_encoding TO 'utf8';
ALTER ROLE sqladmin SET default_transaction_isolation TO 'read committed';
ALTER ROLE sqladmin SET timezone TO 'UTC';
```

Now, we can give our new user access to administer our new database:

```Postgres
GRANT ALL PRIVILEGES ON DATABASE logbook TO sqladmin;
```

Allow the sql user to create a new database for testing:

```
ALTER USER sqladmin CREATEDB;
```

When you are finished, exit out of the PostgreSQL prompt by typing:

```Postgres
\q
```

Postgres is now set up so that Django can connect to and manage its database information.


### Optionnal: Install PGAdmin

Optionnaly, you can install PGAdmin 4 to explore your PostgreSQL instance from
[https://www.pgadmin.org/download/](https://www.pgadmin.org/download/)

### Add the PostgreSQL settings to the project configuration

Once this is done, you now have a PostgreSQL database.

Create a ".env" file at the root of the project, and define the following environment variables in it:

```
export DATABASE_URL=postgres://sqladmin:cholet49300@127.0.0.1:5432/logbook
export CELERY_BROKER_URL=redis://localhost:6379/0
```

By default, Django will load this file (if it exists) at startup and populate the local environment with these settings.

In the future, if you want to disable this behaviour enter in your shell:
```
export DJANGO_READ_DOT_ENV_FILE=False
```
### Apply migrations

Apply the database migrations by running:
```
python manage.py migrate
```

### Start the development server

Run the server with:
```
python manage.py runserver
```
Open your browser at [http://localhost:8000](http://localhost:8000)

## Contribution guidelines

When editing Python files, select "flake8" as the linter in Visual Studio Code. To do this, open any python file, then CRTL-ALT-P to open the command option in VS Code. Select "Python: Select Linter" and select flake8

The flake8 configuration is defined in [setup.cfg](setup.cfg)

## Shortcuts

A Makefile contains several useful shortcuts that can be run using
```
make <option>
```

The following options are available:
- install: create virtual environment and install python packages
- start: start the development server
- make-migrations: generate migrations
- migrate: apply migrations
- test: run the tests