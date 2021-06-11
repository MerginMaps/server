
<p align="center">
<a href="https://public.cloudmergin.com/" target="_blank">
<img src="mergin_logo.png" alt="Mergin" width="400">
</a>
</p>

<p align="center">
	<b>Store and track changes to your geo-data</b>
</p>

<p align="center">
<img src="https://img.shields.io/badge/license-AGPL-blue">
</p>

## About

Mergin is a web platform for storage and synchronisation of geospatial projects across multiple users and devices (desktop and mobile).
The platform is especially useful when you need:

- **Mobile data collection.** If you need to capture location of assets (and their attributes) or update an existing database.

- **Data sharing data.** No complicated setup of access by IT admins to get your data to colleagues or clients. Set up permissions and send invites with few clicks.

- **Offline access.** Work with data with no interruption even without constant Internet connection - sync any changes when you are back online.

- **Collaborative editing.** No more problems dealing with multiple copies of the same dataset in different versions - all changes are automatically consolidated in one place.

- **Audit changes.** Knowing who has changed what and when in a database is often important - Mergin keeps track of the history and allows to go back if needed.

- **No coding required.** Everything can be set up with no knowledge of programming.

Mergin organises all data in projects. A project in Mergin is a directory containing various data files - GeoPackages,
QGIS project files, documents, pictures and more. As soon as a project is uploaded to Mergin, it can be easily accessed directly from the web, from QGIS or from iOS/Android via [Input app](https://inputapp.io/).

## Screenshots

<p align="center">
<b>Mergin web</b><br>
<table align="center">
<tr>
	<td align="center"><img src="web_dashboard.jpg" width=300><br>Dashboard</td>
	<td align="center"><img src="web_files.jpg" width=300><br>Project files</td>
</tr>
<tr>
	<td align="center"><img src="web_history.jpg" width=300><br>Project version history</td>
	<td align="center"><img src="web_settings.jpg" width=300><br>Project settings</td>
</tr>
</table>
</p>

<p align="center">
<b>Mergin in <a href="https://inputapp.io/">Input app</a></b><br>
<img src="input.jpg" height=300>
</p>

<p align="center">
<b>Mergin in QGIS</b><br>
<img src="qgis_browser.jpg" width=600>
</p>

## Features

- 🌍 **Store data** - GeoPackages, QGIS project files, GeoTIFFs, pictures or any other data easily
- 📱 **Phones and tables** - Great for working on field surveys, thanks to [Input app]() based on QGIS, for iPhone, iPad and Android
- 🌟 **QGIS integration** - [Mergin plugin](https://github.com/lutraconsulting/qgis-mergin-plugin) is available to help with project setup and seamless syncing within QGIS
- 👥 **Multi-user editing** - Changes to vector/attribute data from multiple users are automatically merged
- 📖 **Data versioning** - Keeping history of all changes, allowing to go back if needed
- 🔌 **Offline editing** - Clients do not need to be online all the time - only when syncing changes
- 🌱 **Sharing with collaborators** - Projects can be shared with other team members
- 🏰 **Granular permissions** - Decide who can read, write or manage projects
- 🌈 **Web interface** - Simple user interface to view and manage projects
- ⚡️ **Fast** - Efficient sync protocol transfering data between clients and server
- 🧑‍💻 **Developer friendly** - Mergin is open platform. CLI tools and client libraries available for [Python](https://github.com/lutraconsulting/mergin-py-client) and [C++](https://github.com/lutraconsulting/mergin-cpp-client)
- 💽 **Sync with database** - Supporting two-way sync of data with PostGIS using [mergin-db-sync](https://github.com/lutraconsulting/mergin-db-sync) tool
- 👷‍♀️ **Work packages** - Split main database to smaller chunks for teams using [mergin-work-packages](https://github.com/lutraconsulting/mergin-work-packages) tool

Mergin offers a unique combination of features that other tools do not provide out of the box:

- relational databases (such as PostGIS or Oracle) are great for keeping a central repository of spatial data, but offline access, versioning and sharing outside of a single organisation are complicated to set up.

- traditional storage products (like Dropbox or Google Drive) are great for storage of large amounts of data (pictures/videos) and offering offline access, but concurrent access to data (e.g. a single vector layer) is not going to work well.


## Quick start

Try Mergin at https://public.cloudmergin.com/ - the SaaS service run by Lutra Consulting, the makers of Mergin.

TODO: running with docker

## Documentation

For user help and documentation, visit https://help.cloudmergin.com/
If you'd like to contribute and improve the documentation visit https://github.com/lutraconsulting/mergin-docs

## Get in touch

If you need support, a custom deployment, extending the service capabilities and new features do not hesitate to contact us on info@lutraconsulting.co.uk

## License

Mergin is open source and licensed under the terms of AGPL licence.

---


## Running with Docker
Adjust configuration in [docker-compose.yml](docker-compose.yml), e.g. replace 'fixme' entries and run with docker compose:
```shell
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
