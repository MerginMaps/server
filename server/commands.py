# Copyright (C) 2018 Lutra Consulting Limited. All rights reserved.
# GNU Affero General Public License v3.0 - see licence.txt for more details.

import os
import json
import shutil
import click
from datetime import datetime
from sqlalchemy.schema import MetaData
from marshmallow import ValidationError
from wtforms.validators import ValidationError

from src import create_app, db
from src.forms import namespace_validation
from src.auth.models import User, UserProfile
from src.models.db_models import Project
from src.util import is_name_allowed, mergin_secure_filename

app = create_app()


@app.cli.command()
def init_db():
    """Re-creates app's database"""
    print('Database initialization ...')
    db.drop_all(bind=None)
    db.create_all(bind=None)
    print('Done. Tables created.')
    db.session.commit()
    print('Done.')


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()


@app.cli.command()
def dump_db():
    """Dumps data from database in JSON format (to stdout)"""
    metadata = MetaData()
    metadata.reflect(bind=db.engine)

    result = {}
    for table in metadata.sorted_tables:
        result[table.name] = [dict(row) for row in db.engine.execute(table.select())]

    print(json.dumps(result, cls=JsonEncoder, indent=2))


@app.cli.command()
@click.argument('input-file')
def load_db(input_file):
    """Load data from JSON file into the database"""
    with open(input_file) as json_file:
        data = json.load(json_file)

    connection = db.engine.connect()
    trans = connection.begin()
    metadata = MetaData()
    metadata.reflect(bind=db.engine)

    try:
        for table in metadata.sorted_tables:
            items = data.get(table.name, [])
            for item in items:
                connection.execute(table.insert(), **item)
        trans.commit()
    except:
        trans.rollback()
        raise


@app.cli.command()
def check_location_file():
    """ Return log for checking files for every version """
    # Checking every files
    # check every project
    for project in Project.query.all():

        # check every version of project
        for version in project.versions.all():

            # check every file of version
            for _file in version.files:

                location = os.path.join(project.storage.project_dir, _file['location'])
                if os.path.join(project.storage.project_dir, version.name) not in location:
                    continue

                location_after_sanitized = os.path.join(
                    project.storage.project_dir, version.name, mergin_secure_filename(_file['path']))
                if location != location_after_sanitized:
                    print(
                        f'- files not same between original and sanitized `{location}` - `{location_after_sanitized}`')
                    if os.path.exists(location):
                        print(f'- but location found `{location}`')
                else:
                    if not os.path.exists(location):
                        print(f'- location not found : `{location}`')


@app.cli.command()
def check_broken_username():
    """ Return log for broken username """

    # Checking every user
    class UserField(object):
        def __init__(self, data):
            self.data = data

    for user in User.query.all():
        try:
            namespace_validation(
                None, UserField(user.username))
        except ValidationError as e:
            print(f'{user.username} - {e}')


@app.cli.command()
def check_broken_project_name():
    """ Return log for broken project name"""
    for project in Project.query.all():
        if not is_name_allowed(project.name):
            print(f'{project.name}')


@app.cli.command()
def find_projects_with_missing_dirs():
    """ Return broken projects with missing associated projects directories on file system """
    print("Missing project directories: ")
    for project in Project.query.all():
        if not os.path.exists(project.storage.project_dir):
            print(f"{project.namespace}/{project.name}: {project.storage.project_dir}")


@app.cli.command()
@click.argument('username')
@click.argument('password')
@click.option('--is-admin', is_flag=True)
@click.option('--email',  required=True)
def add_user(username, password, is_admin, email):  # pylint: disable=W0612
    """Create user account"""
    create_user(username, password, is_admin, email)


def create_user(username, password, is_admin, email):
    user = User.query.filter_by(username=username).first()
    if user:
        print("ERROR: User {} already exists!\n".format(user.username))

    user = User(username=username, passwd=password, is_admin=is_admin, email=email)
    user.profile = UserProfile()
    user.active = True
    db.session.add(user)
    db.session.commit()


@app.cli.command()
@click.argument('project-name')
@click.option('--version', required=True)
@click.option('--directory', type=click.Path(), required=True)
def download_project(project_name, version, directory):  # pylint: disable=W0612
    """ Download files for project at particular version """
    ns, name = project_name.split('/')
    project = Project.query.filter_by(namespace=ns, name=name).first()
    if not project:
        print("ERROR: Project does not exist")
        return
    pv = next((v for v in project.versions if v.name == version), None)
    if not pv:
        print("ERROR:Project version does not exist")
        return
    if os.path.exists(directory):
        print(f"ERROR: Destination directory {directory} already exist")
        return

    os.mkdir(directory)
    files = pv.files
    for f in files:
        project.storage.restore_versioned_file(f['path'], version)
        f_dir = os.path.dirname(f["path"])
        if f_dir:
            os.makedirs(os.path.join(directory, f_dir), exist_ok=True)
        shutil.copy(os.path.join(project.storage.project_dir, f["location"]), os.path.join(directory, f["path"]))
    print("Project downloaded successfully")
