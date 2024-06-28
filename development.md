
# Mergin Maps Development guide

This page contains useful information for those who wish to develop Mergin.

## Running locally (for dev)
Install dependencies and run services:

### Postgres and Redis

```shell
$ docker run -d --rm --name mergin_maps_dev_db -p 5002:5432 -e POSTGRES_PASSWORD=postgres postgres:14
$ docker run -d --rm --name mergin_maps_dev_redis -p 6379:6379 redis
```

### Server
```shell
$ pip3 install pipenv
$ cd server
# Install dependencies with pipenv
# Note: You can append --three flag in older versions of pipenv (< 3.16.8 2023-02-04)
$ pipenv install --dev
$ export FLASK_APP=application; export COLLECT_STATISTICS=0
$ pipenv run flask init-db
# create admin user
$ pipenv run flask user create admin topsecret --is-admin --email admin@example.com
# create (non admin) user
$ pipenv run flask user create user topsecret --email user@example.com
$ pipenv run celery -A application.celery worker --loglevel=info &
$ pipenv run flask run # run dev server on port 5000
```

### Web applications

Before installing the web applications, make sure you have Node.js installed in a supported version. The applications require Node.js version **18 or higher**.

```shell
$ cd web-app
$ yarn install
$ yarn link:dependencies # link dependencies
$ yarn build:libs # bild libraries @mergin/lib @mergin/admin-lib @mergin/lib-vue2
$ yarn dev  # development client web application dev server on port 8080 (package @mergin/app)
$ yarn dev:admin  # development admin appplication dev server on port 8081 (package @mergin/admin-app)
```

If you are developing a library package (named **-lib*), it is useful to watch the library for changes instead of rebuilding it each time. 

To watch the @mergin/lib library while developing:

```shell
# watch:admin-lib, etc.
yarn watch:lib
# Also watch type definitions
yarn watch:lib:types
```

Watching the type definitions is also useful to pick up any changes to imports or new components that are added.


## Running locally in a docker composition

```shell
# Create the "projects" directory with the current user in order to have the same permissions on the mounted volume
# for this user within the container (if the folder does not exist during startup of the docker composition,
# the docker deamon creates the directory as root, which prevents access for the current user)
mkdir projects

# Run the docker composition as the current user
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose up
```


## Running tests
To launch the unit tests run:
```shell
$ docker run -d --rm --name testing_pg -p 5435:5432 -e POSTGRES_PASSWORD=postgres postgres:14
$ cd server
$ pipenv install --dev --sequential --verbose
$ pipenv run pytest -v --cov=mergin mergin/tests
```
