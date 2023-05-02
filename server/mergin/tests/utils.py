# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import json
import shutil
import uuid
import math
from datetime import datetime
from flask import url_for, current_app
import os
from dateutil.tz import tzlocal

from ..auth.models import User, UserProfile
from ..sync.utils import generate_location, generate_checksum
from ..sync.models import Project, ProjectAccess, ProjectVersion
from ..sync.workspace import GlobalWorkspace
from .. import db
from . import json_headers, DEFAULT_USER, test_project, test_project_dir


def add_user(username, password, is_admin=False):
    """Helper function to create not-privileged user.
    Associated user workspace is created with db hook.

    :param username: username
    :type username: str
    :param password: password
    :type password: str
    :param is_admin: whether user is mergin admin
    :type is_admin: bool
    :returns: User
    """
    user = User(
        username=username,
        passwd=password,
        is_admin=is_admin,
        email=f"{username}@mergin.com",
    )
    user.active = True
    user.verified_email = True
    user.profile = UserProfile()
    db.session.add(user)
    db.session.commit()
    return user


def create_workspace():
    ws = GlobalWorkspace()
    return ws


def login(client, username, password):
    resp = client.post(
        url_for("/.mergin_auth_controller_login"),
        data=json.dumps({"login": username, "password": password}),
        headers=json_headers,
    )
    assert resp.status_code == 200


def create_project(name, workspace, user, **kwargs):
    default_project = {
        "storage_params": {"type": "local", "location": generate_location()},
        "name": name,
    }
    project_params = dict(default_project)
    project_params["creator"] = user
    project_params["workspace"] = workspace

    p = Project(**project_params, **kwargs)
    p.updated = datetime.utcnow()
    db.session.add(p)

    public = kwargs.get("public", False)
    pa = ProjectAccess(p, public)
    db.session.add(pa)

    changes = {"added": [], "updated": [], "removed": []}
    pv = ProjectVersion(p, "v0", user.username, changes, p.files, "127.0.0.1")
    pv.project = p
    db.session.add(pv)
    db.session.commit()

    os.makedirs(p.storage.project_dir, exist_ok=True)
    return p


def cleanup(client, projects_dirs):
    """Clean up project files created at various tests scenarios"""
    for d in projects_dirs:
        path = os.path.join(client.application.config["LOCAL_PROJECTS"], d)
        if os.path.exists(path):
            shutil.rmtree(path)


def login_as_admin(client):
    login(client, "mergin", "ilovemergin")


class Response:
    """Simple mock of requests.response object."""

    def __init__(self, ok, json, headers=None):
        self.ok = ok
        self._json = json
        self.text = f"{json}"
        self.headers = headers or {}
        self.status_code = 200 if ok else 400  # some default not-success code

    def json(self):
        return self._json

    def iter_content(self, chunk_size=1024):
        pass


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()

        return super().default(obj)


def initialize():
    # clean up (in case of previous failures)
    proj_dir = os.path.join(current_app.config["LOCAL_PROJECTS"], DEFAULT_USER[0])
    if os.path.exists(proj_dir):
        shutil.rmtree(proj_dir)

    # add default user/super admin
    user = add_user(DEFAULT_USER[0], DEFAULT_USER[1], is_admin=True)
    workspace = create_workspace()
    # add default tests project for later use
    project_params = {
        "storage_params": {
            "type": "local",
            "location": os.path.join(DEFAULT_USER[0], test_project),
        },
        "name": test_project,
        "creator": user,
        "workspace": workspace,
    }

    p = Project(**project_params)
    p.files = []
    for root, dirs, files in os.walk(
        test_project_dir, topdown=True
    ):  # pylint: disable=W0612
        for f in files:
            abs_path = os.path.join(root, f)
            p.files.append(
                {
                    "path": abs_path.replace(test_project_dir, "").lstrip("/"),
                    "location": os.path.join(
                        "v1", abs_path.replace(test_project_dir, "").lstrip("/")
                    ),
                    "size": os.path.getsize(abs_path),
                    "checksum": generate_checksum(abs_path),
                    "mtime": datetime.fromtimestamp(os.path.getmtime(abs_path)),
                }
            )
    p.latest_version = "v1"
    p.updated = datetime.utcnow()
    db.session.add(p)

    # add default project permissions
    pa = ProjectAccess(p, True)
    db.session.add(pa)
    db.session.commit()

    changes = {"added": p.files, "updated": [], "removed": []}
    pv = ProjectVersion(p, "v1", user.username, changes, p.files, "127.0.0.1")
    db.session.add(pv)
    db.session.commit()

    # mimic files were uploaded
    shutil.copytree(
        os.path.join(test_project_dir),
        os.path.join(proj_dir, test_project, "v1"),
    )


def file_info(project_dir, path, chunk_size=1024):
    """Generate file metadata for mergin upload"""
    abs_path = os.path.join(project_dir, path)
    f_size = os.path.getsize(abs_path)
    return {
        "path": path,
        "checksum": generate_checksum(abs_path),
        "size": f_size,
        "mtime": datetime.fromtimestamp(os.path.getmtime(abs_path), tzlocal()),
        "chunks": [str(uuid.uuid4()) for i in range(math.ceil(f_size / chunk_size))],
    }


def upload_file_to_project(project, filename, client):
    """ Add test file to project - start, upload and finish push process """
    file = os.path.join(test_project_dir, filename)
    assert os.path.exists(file)
    changes = {
        "added": [file_info(test_project_dir, filename)],
        "updated": [],
        "removed": [],
    }
    data = {"version": project.latest_version, "changes": changes}
    resp = client.post(
        f"/v1/project/push/{project.workspace.name}/{project.name}",
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    upload_id = resp.json["transaction"]
    changes = data["changes"]
    file_meta = changes["added"][0]
    for chunk_id in file_meta["chunks"]:
        url = f"/v1/project/push/chunk/{upload_id}/{chunk_id}"
        with open(file, "rb") as f:
            f_data = f.read(1024)
        client.post(
            url, data=f_data, headers={"Content-Type": "application/octet-stream"}
        )
    assert client.post(f"/v1/project/push/finish/{upload_id}").status_code == 200

