# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import json
import shutil
import pysqlite3
import uuid
import math
from dataclasses import asdict
from datetime import datetime
import pysqlite3
from flask import url_for, current_app
import os
from dateutil.tz import tzlocal
from pygeodiff import GeoDiff

from ..auth.models import User, UserProfile
from ..sync.utils import generate_location, generate_checksum
from ..sync.models import (
    Project,
    ProjectVersion,
    FileHistory,
    ProjectRole,
    PushChangeType,
)
from ..sync.files import ProjectFileChange, PushChangeType, files_changes_from_upload
from ..sync.workspace import GlobalWorkspace
from ..app import db
from . import json_headers, DEFAULT_USER, test_project, test_project_dir, TMP_DIR

CHUNK_SIZE = 1024


def add_user(username="random", password="random", is_admin=False) -> User:
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
    """Create new empty project"""
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
    db.session.flush()
    pv = ProjectVersion(p, 0, user.id, [], "127.0.0.1")
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
    project_files = []
    for root, dirs, files in os.walk(
        test_project_dir, topdown=True
    ):  # pylint: disable=W0612
        for f in files:
            abs_path = os.path.join(root, f)
            project_files.append(
                ProjectFileChange(
                    path=abs_path.replace(test_project_dir, "").lstrip("/"),
                    checksum=generate_checksum(abs_path),
                    size=os.path.getsize(abs_path),
                    mtime=str(datetime.fromtimestamp(os.path.getmtime(abs_path))),
                    change=PushChangeType.CREATE,
                    location=os.path.join(
                        "v1", abs_path.replace(test_project_dir, "").lstrip("/")
                    ),
                    diff=None,
                )
            )
    p.latest_version = 1
    p.public = True
    p.set_role(user.id, ProjectRole.OWNER)
    p.updated = datetime.utcnow()
    db.session.add(p)
    db.session.commit()

    pv = ProjectVersion(p, 1, user.id, project_files, "127.0.0.1")
    db.session.add(pv)
    db.session.commit()

    # make sure for history without diff there is a proper Null in database jsonb column
    assert FileHistory.query.filter_by(version_id=pv.id).filter(
        FileHistory.changes != PushChangeType.UPDATE_DIFF.value
    ).count() == len(project_files)

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


def mock_changes_data(project, filename) -> dict:
    changes = {
        "added": [file_info(test_project_dir, filename)],
        "updated": [],
        "removed": [],
    }
    data = {
        "version": ProjectVersion.to_v_name(project.latest_version),
        "changes": changes,
    }
    return data


def push_file_start(
    project: Project, filename: str, client, mocked_changes_data=None
) -> dict:
    """
    Initiate the process of pushing a file to a project by calling /push endpoint.
    """
    file = os.path.join(test_project_dir, filename)
    assert os.path.exists(file)
    data = mocked_changes_data or mock_changes_data(project, filename)
    resp = client.post(
        f"/v1/project/push/{project.workspace.name}/{project.name}",
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    return resp


def upload_file_to_project(project: Project, filename: str, client) -> dict:
    """Add test file to project - start, upload and finish push process"""
    file = os.path.join(test_project_dir, filename)
    data = mock_changes_data(project, filename)
    changes = data.get("changes")
    resp = push_file_start(project, filename, client, data)
    upload_id = resp.json["transaction"]
    file_meta = changes["added"][0]
    for chunk_id in file_meta["chunks"]:
        url = f"/v1/project/push/chunk/{upload_id}/{chunk_id}"
        with open(file, "rb") as f:
            f_data = f.read(1024)
        client.post(
            url, data=f_data, headers={"Content-Type": "application/octet-stream"}
        )
    push_finish = client.post(f"/v1/project/push/finish/{upload_id}")
    assert resp.status_code == 200
    assert push_finish.status_code == 200
    return push_finish


def gpkgs_are_equal(file1, file2):
    """Check two geopackge files are equal by means there are no geodiff changes."""
    changes = os.path.join(TMP_DIR, "changeset" + str(uuid.uuid4()))
    geodiff = GeoDiff()
    geodiff.create_changeset(file1, file2, changes)
    return not geodiff.has_changes(changes)


def execute_query(file, sql):
    """Open connection to gpkg file and execute SQL query"""
    gpkg_conn = pysqlite3.connect(file)
    gpkg_conn.enable_load_extension(True)
    gpkg_cur = gpkg_conn.cursor()
    gpkg_cur.execute('SELECT load_extension("mod_spatialite")')
    gpkg_cur.execute(sql)
    gpkg_conn.commit()
    gpkg_conn.close()


def create_blank_version(project):
    """Helper to create dummy project version with no changes to increase count"""
    pv = ProjectVersion(
        project,
        project.next_version(),
        project.creator.id,
        [],
        "127.0.0.1",
    )
    db.session.add(pv)
    db.session.commit()


def push_change(project, action, path, src_dir):
    """Helper to create ProjectVersion incl. files changes based on change metadata

    :param project: project to push, Project
    :param action: change action type, str
    :param path: relative path of file inside project, str
    :param src_dir: absolute path to directory with file upload, StrPath

    :returns: new project version, ProjectVersion
    """
    current_files = project.files
    new_version = ProjectVersion.to_v_name(project.next_version())
    changes = {"added": [], "updated": [], "removed": []}
    metadata = {**file_info(src_dir, path), "location": os.path.join(new_version, path)}

    if action == "added":
        new_file = os.path.join(project.storage.project_dir, metadata["location"])
        os.makedirs(os.path.dirname(new_file), exist_ok=True)
        shutil.copy(os.path.join(src_dir, metadata["path"]), new_file)
        changes["added"].append(metadata)
    elif action == "updated":
        f_updated = next(f for f in current_files if f.path == path)
        metadata = {
            **file_info(src_dir, path),
            "location": os.path.join(new_version, path),
        }
        patched_file = os.path.join(project.storage.project_dir, metadata["path"])
        os.makedirs(os.path.dirname(patched_file), exist_ok=True)
        if ".gpkg" in path:
            diff_id = str(uuid.uuid4())
            diff_name = path + "-diff-" + diff_id
            basefile = os.path.join(project.storage.project_dir, f_updated.location)
            modfile = os.path.join(src_dir, path)
            changeset = os.path.join(src_dir, diff_name)
            project.storage.geodiff.create_changeset(basefile, modfile, changeset)
            metadata["diff"] = {
                "path": diff_name,
                "checksum": generate_checksum(changeset),
                "size": os.path.getsize(changeset),
                "chunks": [
                    str(uuid.uuid4())
                    for i in range(
                        math.ceil(file_info(src_dir, diff_name)["size"] / CHUNK_SIZE)
                    )
                ],
                "location": os.path.join(new_version, diff_name),
            }
            diff_file = os.path.join(
                project.storage.project_dir, metadata["diff"]["location"]
            )
            os.makedirs(os.path.dirname(diff_file), exist_ok=True)
            shutil.copy(changeset, diff_file)

        new_file = os.path.join(project.storage.project_dir, metadata["location"])
        os.makedirs(os.path.dirname(new_file), exist_ok=True)
        shutil.copy(os.path.join(src_dir, metadata["path"]), new_file)
        changes["updated"].append(metadata)
    elif action == "removed":
        f_removed = next(f for f in current_files if f.path == path)
        changes["removed"].append(asdict(f_removed))
    else:
        return

    file_changes = files_changes_from_upload(
        changes, location_dir=f"v{project.next_version()}"
    )
    pv = ProjectVersion(
        project,
        project.next_version(),
        project.creator.id,
        file_changes,
        "127.0.0.1",
    )
    db.session.add(pv)
    db.session.commit()
    assert pv.project_size == sum(file.size for file in pv.files)
    db.session.add(project)
    db.session.commit()
    return pv


def modify_file_times(path, time: datetime, accessed=True, modified=True):
    """Modifies files access and modification time

    :param path: path to file to be modified
    :param time: new time - seconds since the epoch
    :param accessed: modify access time
    :param modified: modify modification time
    """
    file_stat = os.stat(path)
    epoch_time = time.timestamp()
    atime = epoch_time if accessed else file_stat.st_atime
    mtime = epoch_time if modified else file_stat.st_mtime

    os.utime(path, (atime, mtime))
