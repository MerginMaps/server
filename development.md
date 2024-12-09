
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
$ pip3 install --upgrade pip==24.0
$ pip3 install pipenv==2024.0.1
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

If you want to run the whole stack locally, you can use the docker. Docker will build the images from yout local files and run the services.

```shell
# Run the docker composition with the current Dockerfiles
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Give ownership of the ./projects folder to user that is running the gunicorn container
sudo chown 901:999 projects/

# init db and create user
docker exec -it merginmaps-server flask init-db
docker exec -it merginmaps-server flask user create admin topsecret --is-admin --email admin@example.com
```

To check if application is running, you can use following mand to verify you installation:

```shell
docker exec -it merginmaps-server flask server check
```

To check if emails are sending correctly, you can use following mand to verify you installation:

```shell
docker exec -it merginmaps-server flask server send-check-email --email  admin@example.com
```

In docker-compose.dev.yml is started maildev/maildev image that can be used to test emails (see [https://github.com/maildev/maildev/](https://github.com/maildev/maildev/)). In localhost:1080 you can see the emails sent by the application in web interface.

## Running tests
To launch the unit tests run:
```shell
$ docker run -d --rm --name testing_pg -p 5435:5432 -e POSTGRES_PASSWORD=postgres postgres:14
$ cd server
$ pipenv install --dev --sequential --verbose
$ pipenv run pytest -v --cov=mergin mergin/tests
```
