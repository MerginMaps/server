# Copyright (C) 2020 Lutra Consulting Limited. All rights reserved.
# Do not distribute without the express permission of the author.

import json
import shutil
from datetime import datetime
from flask import url_for, current_app
import os
from sqlalchemy import or_
from sqlalchemy.orm.attributes import flag_modified

from src.auth.models import User, UserProfile
from src.mergin_utils import generate_location, generate_checksum
from src.models.db_models import Project, ProjectAccess, ProjectVersion, Namespace, ProjectTransfer, Account
from src.organisation.models import Organisation
from src import db
from . import json_headers, DEFAULT_USER, test_project, test_project_dir


def add_user(username, password, is_admin=False):
    """ Helper function to create not-privileged user.
    Associated user namespace is created with db hook.

    :param username: username
    :type username: str
    :param password: password
    :type password: str
    :param is_admin: whether user is mergin admin
    :type is_admin: bool
    :returns: User
    """
    user = User(username=username, passwd=password, is_admin=is_admin, email=f"{username}@mergin.com")
    user.active = True
    user.verified_email = True
    user.profile = UserProfile()
    db.session.add(user)
    db.session.commit()
    return user


def login(client, username, password):
    resp = client.post(
        url_for('auth.login'),
        data=json.dumps({'login': username, 'password': password}),
        headers=json_headers
    )
    assert resp.status_code == 200


def create_project(name, namespace, user, **kwargs):
    default_project = {"storage_params": {"type": "local", "location": generate_location()}, "name": name}
    project_params = dict(default_project)
    project_params['creator'] = user
    project_params['namespace'] = namespace

    p = Project(**project_params, **kwargs)
    p.updated = datetime.utcnow()
    db.session.add(p)

    public = kwargs.get("public", False)
    pa = ProjectAccess(p, public)
    db.session.add(pa)

    changes = {"added": [], "renamed": [], "updated": [], "removed": []}
    pv = ProjectVersion(p, 'v0', user.username, changes, p.files, '127.0.0.1')
    p.versions.append(pv)
    db.session.commit()

    os.makedirs(p.storage.project_dir, exist_ok=True)
    return p


def cleanup(client, projects_dirs):
    """ Clean up project files created at various test scenarios """
    for d in projects_dirs:
        path = os.path.join(client.application.config['LOCAL_PROJECTS'], d)
        if os.path.exists(path):
            shutil.rmtree(path)


def login_as_admin(client):
    login(client, 'mergin', 'ilovemergin')


def share_project(project, user):
    project.access.owners.append(user.id)
    project.access.writers.append(user.id)
    project.access.readers.append(user.id)
    flag_modified(project.access, "owners")
    flag_modified(project.access, "writers")
    flag_modified(project.access, "readers")
    db.session.add(project)
    db.session.commit()


def transfer_project(project, to_namespace):
    project_transfer = ProjectTransfer(project, to_namespace, project.creator_id)
    db.session.add(project_transfer)
    db.session.commit()
    return project_transfer


def get_shared_projects(user):
    projects = Project.query.filter(Project.namespace != user.username).filter(
        or_(Project.access.has(ProjectAccess.owners.contains([user.id])),
            Project.access.has(ProjectAccess.writers.contains([user.id])),
            Project.access.has(ProjectAccess.readers.contains([user.id])))
    ).all()
    return projects


def create_organisation(name, owner):
    org = Organisation(name=name, creator_id=owner.id)
    db.session.add(org)
    db.session.commit()
    return org


class Response:
    """ Simple mock of requests.response object. """
    def __init__(self, ok, json):
        self.ok = ok
        self._json = json
        self.text = f'{json}'

    def json(self):
        return self._json


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()

        return super().default(obj)


def initialize():
    # clean up (in case of previous failures)
    proj_dir = os.path.join(current_app.config['LOCAL_PROJECTS'], DEFAULT_USER[0])
    if os.path.exists(proj_dir):
        shutil.rmtree(proj_dir)

    # add default user/super admin
    user = add_user(DEFAULT_USER[0], DEFAULT_USER[1], is_admin=True)

    # add default test project for later use
    project_params = {
        "storage_params": {"type": "local", "location": os.path.join(DEFAULT_USER[0], test_project)},
        "name": test_project,
        "creator": user,
        "namespace": user.username
    }

    p = Project(**project_params)
    p.files = []
    for root, dirs, files in os.walk(test_project_dir, topdown=True):  # pylint: disable=W0612
        for f in files:
            abs_path = os.path.join(root, f)
            p.files.append({
                'path': abs_path.replace(test_project_dir, '').lstrip('/'),
                'location': os.path.join('v1', abs_path.replace(test_project_dir, '').lstrip('/')),
                'size': os.path.getsize(abs_path),
                'checksum': generate_checksum(abs_path),
                'mtime': datetime.fromtimestamp(os.path.getmtime(abs_path))
            })
    p.latest_version = "v1"
    db.session.add(p)

    # add default project permissions
    pa = ProjectAccess(p, True)
    db.session.add(pa)
    db.session.commit()

    changes = {"added": p.files, "renamed": [], "updated": [], "removed": []}
    pv = ProjectVersion(p, 'v1', user.username, changes, p.files, '127.0.0.1')
    db.session.add(pv)
    db.session.commit()

    # mimic files were uploaded
    shutil.copytree(os.path.join(current_app.config['TEST_DIR'], test_project),
                    os.path.join(proj_dir, test_project, 'v1'))
