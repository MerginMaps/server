
# Mergin Maps Development guide

This page contains useful information for those who wish to develop Mergin.

## Running locally (for dev)
Install dependencies and run services:

### Python and Node.js

Required versions are pinned in `.tool-versions` in the repository root. With [asdf](https://asdf-vm.com) or [mise](https://mise.jdx.dev) installed, run in the repository root:

```shell
$ asdf install  # or: mise install
$ corepack enable  # provides yarn
```

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
$ pipenv install --categories telemetry
$ pipenv run pre-commit install
$ pipenv run pre-commit run --all-files
# dev settings, secrets and salts have no defaults
# not named .env on purpose: pipenv and flask would load it automatically, also into tests
$ cat > .dev.env <<EOF
FLASK_APP=application
COLLECT_STATISTICS=0
SECRET_KEY=$(python3 -c 'import secrets;print(secrets.token_hex(32))')
SECURITY_PASSWORD_SALT=$(python3 -c 'import secrets;print(secrets.token_hex(16))')
SECURITY_EMAIL_SALT=$(python3 -c 'import secrets;print(secrets.token_hex(16))')
SECURITY_BEARER_SALT=$(python3 -c 'import secrets;print(secrets.token_hex(16))')
SECURITY_UNLOCK_SALT=$(python3 -c 'import secrets;print(secrets.token_hex(16))')
MAIL_DEFAULT_SENDER=dev@localhost
MERGIN_BASE_URL=http://localhost:8080
EOF
# let pipenv load it for commands in this shell
$ export PIPENV_DOTENV_LOCATION=$PWD/.dev.env
# folder for project files (LOCAL_PROJECTS default)
$ mkdir -p ../projects
$ pipenv run flask init-db
# create admin user
$ pipenv run flask user create admin topsecret --is-admin --email admin@example.com
# create (non admin) user
$ pipenv run flask user create user topsecret --email user@example.com
$ pipenv run celery -A application.celery worker --loglevel=info &
$ pipenv run flask run # run dev server on port 5000
```

### Web applications

Before installing the web applications, make sure you have Node.js installed in a supported version. The applications require Node.js version **22 or higher**.

```shell
$ cd web-app
$ yarn install
$ yarn link:dependencies # link dependencies
$ yarn build:libs # bild libraries @mergin/lib @mergin/admin-lib @mergin/lib-vue2
$ yarn dev  # development client web application dev server on port 8080 (package @mergin/app)
$ yarn dev:admin  # development admin application dev server on port 8081 (package @mergin/admin-app)
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

If you want to run the whole stack locally, you can use the docker. Docker will build the images from your local files and run the services.

```shell
# Enter community edition deployment folder
cd deployment/community/

# Create .prod.env file from .env.template
cp .env.template .prod.env

docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Give ownership of the ./projects folder to user that is running the gunicorn container
sudo chown 901:999 projects

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

### Running with remote debugger
If you want to run the application with remote debugger, you can use debug compose file with attached source code and reload.
It starts a debugpy session on port 5678 you can attach to.

```shell
docker compose -f docker-compose.yml -f docker-compose.debug.yml up
```

## Running tests
To launch the unit tests run:
```shell
$ docker run -d --rm --name testing_pg -p 5435:5432 -e POSTGRES_PASSWORD=postgres postgres:14
$ cd server
$ pipenv install --dev --sequential --verbose
# tests use .test.env only, do not load dev settings (e.g. exported PIPENV_DOTENV_LOCATION)
$ PIPENV_DONT_LOAD_ENV=1 pipenv run pytest -v --cov=mergin mergin/tests
```
