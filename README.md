
![mergin](mergin_logo.png)

https://public.cloudmergin.com/

Store and track changes to your geo-data

## Running with Docker
Adjust configuration, e.g. replace 'fixme' entries:
```shell
$ cp mergin.env.template mergin.env
```

Run with docker compose:
```shell
$ export TAG=2021.6  # specify version
$ docker-compose up
$ docker exec -it mergin-server flask init-db
$ docker exec -it mergin-server flask add-user admin topsecret --is-admin --email admin@example.com
$ sudo chown -R  901:999 ./projects/
$ sudo chmod g+s ./projects/
```
Projects are saved locally in `./projects` folder.

## Running locally (for dev)
Install dependencies and run services:

```shell
$ docker run -d --rm --name mergin_db -p 5002:5432 -e POSTGRES_PASSWORD=postgres postgres:10
$ docker run -d --rm --name redis -p 6379:6379 redis
```

### Server
```shell
$ pip3 install pipenv
$ cd server
$ pipenv install --dev --three
$ pipenv run flask init-db
$ pipenv run flask add-user admin topsecret --is-admin --email admin@example.com
$ pipenv run celery worker -A src.run_celery.celery --loglevel=info &
$ pipenv run flask run # run dev server on port 5000
```

### Web app
```shell
$ sudo apt install nodejs
$ cd web-app
$ npm install
$ npm run serve
```
and open your browser to here:
```
http://localhost:8080
```

## Running tests
To launch the unit tests run:
```shell
$ docker run -d --rm --name testing_pg -p 5435:5432 -e POSTGRES_PASSWORD=postgres postgres:10
$ cd server
$ pipenv run pytest --cov-report html --cov=src test
```