
# Mergin Maps Development

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

### Web app
```shell
$ sudo apt install nodejs
$ cd web-app
$ yarn install
$ yarn link:dependencies # link dependencies
$ yarn build:libs
$ yarn serve  # development client app server on port 8080
$ yarn serve:admin  # development admin app server on port 8081
```

## Running tests
To launch the unit tests run:
```shell
$ docker run -d --rm --name testing_pg -p 5435:5432 -e POSTGRES_PASSWORD=postgres postgres:14
$ cd server
$ pipenv install --dev --sequential --verbose
$ pipenv run pytest -v --cov=mergin mergin/tests
```
