# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import datetime
import os
import pysqlite3
from unittest.mock import patch
import pytest
import json
import uuid
import math
import time
import hashlib
import shutil
import re
from pygeodiff import GeoDiff
from flask import url_for, current_app
import tempfile

from sqlalchemy import desc
from sqlalchemy.orm.attributes import flag_modified
from .. import db
from ..sync.models import (
    Project,
    Upload,
    ProjectVersion,
    ProjectAccess,
    SyncFailuresHistory,
    GeodiffActionHistory,
    ProjectRole,
)
from ..sync.schemas import ProjectListSchema
from ..sync.utils import generate_checksum, is_versioned_file
from ..auth.models import User, UserProfile

from . import (
    test_project,
    test_workspace_name,
    test_workspace_id,
    test_project_dir,
    json_headers,
    TMP_DIR,
)
from .utils import (
    add_user,
    create_project,
    create_workspace,
    DateTimeEncoder,
    login,
    file_info,
    login_as_admin,
)
from ..config import Configuration
from ..sync.config import Configuration as SyncConfiguration
from ..sync.utils import get_project_path

CHUNK_SIZE = 1024


def test_file_history(client, diff_project):
    resp = client.get(
        "/v1/resource/history/{}/{}?path={}".format(
            test_workspace_name, test_project, "test.gpkg"
        )
    )
    history = resp.json["history"]
    assert resp.status_code == 200
    assert "v2" not in history
    assert "v8" not in history
    assert history["v9"]["change"] == "added"

    # tests we can reproduce above with 'since' param in project details endpoint
    resp = client.get(
        "/v1/project/{}/{}?since=v1".format(test_workspace_name, test_project)
    )
    test_gpkg_history = next(
        f["history"] for f in resp.json["files"] if f["path"] == "test.gpkg"
    )
    assert resp.status_code == 200
    assert "v2" not in test_gpkg_history
    assert "v8" not in test_gpkg_history
    assert test_gpkg_history["v9"]["change"] == "added"

    resp = client.get(
        "/v1/project/{}/{}?since=v4".format(test_workspace_name, test_project)
    )
    test_gpkg_history = next(
        f["history"] for f in resp.json["files"] if f["path"] == "test.gpkg"
    )
    assert resp.status_code == 200
    assert "v3" not in test_gpkg_history
    assert test_gpkg_history["v9"]["change"] == "added"

    # check geodiff changeset in project version object
    resp = client.get(
        f"/v1/project/versions/paginated/{test_workspace_name}/{test_project}?page=1&per_page=10"
    )
    version_info = next(v for v in resp.json["versions"] if v["name"] == "v7")
    assert "changesets" in version_info
    # the only diff update in version v7 is base.gpkg
    assert len(version_info["changesets"].keys()) == 1
    assert "base.gpkg" in version_info["changesets"]
    assert "summary" in version_info["changesets"]["base.gpkg"]
    assert "size" in version_info["changesets"]["base.gpkg"]
    # tests when no diffs were applied
    resp = client.get(
        f"/v1/project/versions/paginated/{test_workspace_name}/{test_project}?page=1&per_page=10"
    )
    version_info = next(v for v in resp.json["versions"] if v["name"] == "v10")
    assert not version_info["changesets"]

    # not geodiff file -> empty history
    resp = client.get(
        "/v1/resource/history/{}/{}?path={}".format(
            test_workspace_name, test_project, "test_dir/test2.txt"
        )
    )
    assert resp.status_code == 200
    assert not resp.json["history"]

    # not existing file
    resp = client.get(
        "/v1/resource/history/{}/{}?path={}".format(
            test_workspace_name, test_project, "not_existing.txt"
        )
    )
    assert resp.status_code == 404

    # actually is it not possible list history of deleted files (base.gpkg), need to modify Project.file_history()
    resp = client.get(
        "/v1/resource/history/{}/{}?path={}".format(
            test_workspace_name, test_project, "base.gpkg"
        )
    )
    history = resp.json["history"]
    assert resp.status_code == 200
    assert "v3" not in history
    assert history["v9"]["change"] == "removed"
    assert "v10" not in history
    assert "v1" not in history

    # remove two last versions to mimic project ends with v8 (and thus base.gpkg exists)
    versions = (
        ProjectVersion.query.filter_by(project_id=diff_project.id)
        .order_by(desc(ProjectVersion.created))
        .all()
    )
    db.session.delete(versions[0])
    db.session.delete(versions[1])
    diff_project.files = versions[2].files
    diff_project.latest_version = "v8"
    db.session.commit()
    resp = client.get(
        "/v1/resource/history/{}/{}?path={}".format(
            test_workspace_name, test_project, "base.gpkg"
        )
    )
    history = resp.json["history"]
    assert resp.status_code == 200
    assert "v1" not in history
    assert "v3" in history
    assert "location" not in history["v7"]
    assert "expiration" in history["v7"]

    # tests to delete user and account with all of depended entries
    # user delete -> profile  + do project -> (version, upload, access)
    # User.query.filter_by(username="mergin").delete()
    db.session.commit()
    project = Project.query.first()
    upload = Upload.query.first()
    # FIXME cascade was removed: assert not project
    assert not upload


def test_get_paginated_projects(client):
    user = User.query.filter_by(username="mergin").first()
    test_workspace = create_workspace()
    for i in range(14):
        create_project("foo" + str(i), test_workspace, user)

    resp = client.get("/v1/project/paginated?page=1&per_page=10")
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    assert len(resp_data.get("projects")) == 10
    assert resp_data.get("count") == 15
    assert "foo8" in resp_data.get("projects")[9]["name"]
    assert "v0" == resp_data.get("projects")[9]["version"]

    resp = client.get(
        "/v1/project/paginated?page=1&per_page=10&order_params=updated_desc"
    )
    resp_data = json.loads(resp.data)
    assert resp_data.get("projects")[0]["name"] == "foo13"

    resp = client.get(
        "/v1/project/paginated?page=2&per_page=10&order_params=workspace_id_asc,updated_desc"
    )
    resp_data = json.loads(resp.data)
    assert len(resp_data.get("projects")) == 5
    assert resp_data.get("count") == 15
    assert resp_data.get("projects")[4]["name"] == "test"

    # order by workspace name
    resp = client.get(
        "/v1/project/paginated?page=2&per_page=10&order_params=workspace_asc"
    )
    resp_data = json.loads(resp.data)
    assert len(resp_data.get("projects")) == 5
    assert "foo13" in resp_data.get("projects")[-1]["name"]
    # tests backward compatibility sort
    resp_alt = client.get(
        "/v1/project/paginated?page=2&per_page=10&order_by=namespace&descending=false"
    )
    assert resp_alt.json == resp.json

    # try with unknown order parameter
    resp = client.get(
        "/v1/project/paginated?page=2&per_page=10&order_params=tralala_asc,updated_desc"
    )
    resp_data = json.loads(resp.data)
    assert len(resp_data.get("projects")) == 5
    assert resp_data.get("projects")[4]["name"] == "test"

    resp = client.get(
        "/v1/project/paginated?page=1&per_page=10&order_params=updated_desc&namespace=foo1"
    )
    resp_data = json.loads(resp.data)
    assert resp_data.get("count") == 0

    resp = client.get("/v1/project/paginated?page=1&per_page=10&name=foo1")
    resp_data = json.loads(resp.data)
    assert resp_data.get("count") == 5

    resp = client.get("/v1/project/paginated?page=1&per_page=101&name=foo1")
    assert resp.status_code == 400
    assert "101 is greater than the maximum of 100" in resp.json.get("detail")

    # in single namespace approach there cannot be projects in other namespace
    resp = client.get("/v1/project/paginated?page=1&per_page=10&only_namespace=user2")
    assert resp.status_code == 200
    assert resp.json.get("count") == 0

    resp = client.get("/v1/project/paginated?page=1&per_page=10&only_public=true")
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert resp_data.get("count") == 1

    resp = client.get(
        "/v1/project/paginated?page=1&per_page=10&name=foo_a&public=false"
    )
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert len(resp_data.get("projects")) == 0

    resp = client.get("/v1/project/paginated?page=1&per_page=15&name=test")
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert resp_data.get("count") == 1
    assert not resp_data.get("projects")[0].get("has_conflict")

    # tests if project contains conflict files
    project = Project.query.filter(Project.name == "test").first()
    files = project.files.copy()
    files.append(
        {
            "checksum": "89469a6482267de394c7c7270cb7ffafe694ea76",
            "location": "v1/base.gpkg_rebase_conflicts",
            "mtime": "2021-04-14T17:33:32.766731Z",
            "path": "base.gpkg_rebase_conflicts",
            "size": 98304,
        }
    )
    project.files = files
    db.session.commit()

    resp = client.get("/v1/project/paginated?page=1&per_page=15&name=test")
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert resp_data.get("count") == 1
    assert resp_data.get("projects")[0].get("has_conflict")

    # remove conflict copy file
    files = project.files.copy()
    files.remove([f for f in files if f.get("path") == "base.gpkg_rebase_conflicts"][0])
    project.files = files
    db.session.commit()

    resp = client.get("/v1/project/paginated?page=1&per_page=15&name=test")
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert resp_data.get("count") == 1
    assert not resp_data.get("projects")[0].get("has_conflict")

    project.access.public = True
    db.session.commit()

    # reset permissions so new user would be only a guest
    Configuration.GLOBAL_READ = False
    Configuration.GLOBAL_WRITE = False
    Configuration.GLOBAL_ADMIN = False
    # add new user and let him create one project
    user2 = add_user("user2", "ilovemergin")
    assert not test_workspace.user_has_permissions(user2, "read")
    create_project("created", test_workspace, user2)
    login(client, "user2", "ilovemergin")
    # check one project is 'created', none is 'shared'
    resp = client.get("/v1/project/paginated?page=1&per_page=10&flag=created")
    assert resp.json["count"] == 1
    assert resp.json["projects"][0]["name"] == "created"
    resp = client.get("/v1/project/paginated?page=1&per_page=10&flag=shared")
    assert resp.json["count"] == 0
    # share project explicitly
    p = Project.query.filter_by(name="foo1").first()
    p.access.set_role(user2.id, ProjectRole.READER)
    db.session.commit()
    resp = client.get("/v1/project/paginated?page=1&per_page=10&flag=shared")
    assert resp.json["count"] == 1
    assert resp.json["projects"][0]["name"] == "foo1"

    # make user reader of all projects
    Configuration.GLOBAL_READ = True
    resp = client.get("/v1/project/paginated?page=1&per_page=20&flag=shared")
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert resp_data.get("count") == 15  # user sees everything in workspace as shared
    # if removed shared flag, also his created project appears
    resp = client.get("/v1/project/paginated?page=1&per_page=20")
    assert resp.json["count"] == 16

    # inactive user should not see anything but public projects
    user2.active = False
    db.session.commit()
    resp = client.get("/v1/project/paginated?page=1&per_page=20")
    resp_data = json.loads(resp.data)
    assert resp.status_code == 200
    assert resp_data.get("count") == 1
    assert resp_data.get("projects")[0].get("name") == "test"

    # logout - private projects is not listed
    client.get("/app/auth/logout")
    resp_desc = client.get("/v1/project/paginated?page=1&per_page=10")
    assert resp_desc.status_code == 200
    assert len(resp_desc.json["projects"]) == 1

    # mark public project as deleted
    project.removed_at = datetime.datetime.utcnow()
    db.session.commit()
    resp = client.get(
        "/v1/project/paginated?page=1&per_page=10&only_public=true&order_params=namespace_asc"
    )
    assert resp.json.get("count") == 0
    # delete permanently
    project.delete()
    db.session.commit()
    resp = client.get(
        "/v1/project/paginated?page=1&per_page=10&only_public=true&order_params=namespace_asc"
    )
    assert resp.json.get("count") == 0


def test_get_projects_by_names(client):
    user = User.query.filter_by(username="mergin").first()
    test_workspace = create_workspace()
    create_project("foo", test_workspace, user)
    add_user("user2", "ilovemergin")
    user2 = User.query.filter_by(username="user2").first()
    test_workspace_2 = create_workspace()
    create_project("other", test_workspace_2, user2)

    data = {"projects": ["mergin/foo", "user2/other", "something"]}
    resp = client.post(
        "/v1/project/by_names", data=json.dumps(data), headers=json_headers
    )
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    assert resp_data.get("mergin/foo").get("name") == "foo"
    assert resp_data.get("user2/other").get("error") == 404
    assert resp_data.get("something").get("error") == 404


add_project_data = [
    (
        {"name": " foo ", "template": test_project},
        200,
    ),  # valid project name, whitespace will be removed
    ({"name": "foo/bar", "template": test_project}, 400),  # invalid project name
    ({"name": "ba%r", "template": test_project}, 400),  # invalid project name
    ({"name": "bar*", "template": test_project}, 400),  # invalid project name
    ({"name": "support", "template": test_project}, 400),  # forbidden project name
    ({"name": test_project}, 409),
]


@pytest.mark.parametrize("data,expected", add_project_data)
def test_add_project(client, app, data, expected):
    # create new version with diff
    upload, upload_dir = create_transaction(
        "mergin", _get_changes_with_diff(test_project_dir)
    )
    upload_chunks(upload_dir, upload.changes)
    resp = client.post("/v1/project/push/finish/{}".format(upload.id))
    assert resp.status_code == 200

    # add TEMPLATES user and make him creator of test_project (to become template)
    user = User(
        username="TEMPLATES",
        passwd="templates",
        is_admin=False,
        email="templates@mergin.com",
    )
    user.active = True
    db.session.add(user)
    template = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()
    template.creator = user
    db.session.commit()

    resp = client.post(
        "/v1/project/{}".format(test_workspace_name),
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == expected
    if expected == 200:
        project = Project.query.filter_by(
            name=data["name"].strip(), workspace_id=test_workspace_id
        ).first()
        assert not any(
            x["checksum"] != y["checksum"] and x["path"] != y["path"]
            for x, y in zip(project.files, template.files)
        )
        pv = project.get_latest_version()
        assert pv.user_agent is not None
        assert pv.device_id == json_headers["X-Device-Id"]
        # check if there is no diffs in cloned files
        assert not any("diff" in file for file in project.files)
        assert not any("diff" in file for file in pv.files)
        assert pv.changes.get("removed") == []
        assert pv.changes.get("updated") == []
        assert "diff" not in pv.changes.get("added")
        shutil.rmtree(
            os.path.join(app.config["LOCAL_PROJECTS"], project.storage.project_dir)
        )  # cleanup


def test_versioning(client):
    # tests if blank project has version set up to v0
    resp = client.post(
        "/v1/project/{}".format(test_workspace_name),
        data=json.dumps({"name": "version_test"}),
        headers=json_headers,
    )
    assert resp.status_code == 200
    project = Project.query.filter_by(
        name="version_test", workspace_id=test_workspace_id
    ).first()
    pv = project.get_latest_version()
    assert pv.name == "v0"
    assert pv.project_size == 0
    assert pv.device_id == json_headers["X-Device-Id"]


def test_delete_project(client):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    project_dir = project.storage.project_dir
    # mimic update of project with chunk upload
    changes = _get_changes(test_project_dir)
    upload, upload_dir = create_transaction("mergin", changes)
    os.mkdir(os.path.join(upload.project.storage.project_dir, "v2"))
    os.makedirs(os.path.join(upload_dir, "chunks"))
    for f in upload.changes["added"] + upload.changes["updated"]:
        with open(os.path.join(test_project_dir, f["path"]), "rb") as in_file:
            for chunk in f["chunks"]:
                with open(os.path.join(upload_dir, "chunks", chunk), "wb") as out_file:
                    out_file.write(in_file.read(CHUNK_SIZE))

    resp = client.post("/v1/project/push/finish/{}".format(upload.id))
    assert resp.status_code == 200

    # try force delete for active project
    assert (
        client.delete(f"/app/project/removed-project/{project.id}").status_code == 400
    )

    # remove project
    admin = User.query.filter_by(username="mergin").first()
    original_creator_id = project.creator_id
    resp = client.delete("/v1/project/{}/{}".format(test_workspace_name, test_project))
    assert resp.status_code == 200
    rp = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    assert rp.removed_at
    assert rp.removed_by == admin.id
    assert os.path.exists(
        project_dir
    )  # files not deleted yet, since there is possibility of restore
    assert rp.creator_id == original_creator_id

    # do permanent delete as admin by forcing removal
    resp = client.delete(f"/app/project/removed-project/{project.id}")
    assert resp.status_code == 204
    assert not Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).count()
    assert not os.path.exists(project_dir)
    rm_project = Project.query.get(project.id)
    assert rm_project.removed_at and not rm_project.storage_params
    # try to delete again
    resp = client.delete(f"/app/project/removed-project/{rm_project.id}")
    assert resp.status_code == 404


test_project_data = [
    (
        {
            "storage_params": {"type": "local", "location": "some_test"},
            "name": test_project,
        },
        200,
    ),
    ({"storage_params": {"type": "local", "location": "foo"}, "name": "bar"}, 404),
]


@pytest.mark.parametrize("data,expected", test_project_data)
def test_get_project(client, data, expected):
    resp = client.get("/v1/project/{}/{}".format(test_workspace_name, data["name"]))
    assert resp.status_code == expected
    if expected == 200:
        resp_data = json.loads(resp.data)
        assert test_project in resp_data["name"]
        assert len(resp_data["access"]["owners"])
        owner = User.query.get(resp_data["access"]["owners"][0])
        assert resp_data["access"]["ownersnames"][0] == owner.username
        assert resp_data["role"] == "owner"
        resp = client.get("/v1/project/by_uuid/{}".format(resp_data["id"]))
        assert resp.json["role"] == "owner"


test_history_data = [
    ("v9", {"file": {"path": "test.gpkg"}, "versions": ["v9"]}),
    # actually is it not possible list history of deleted files, need to modify Project.file_history()
    # ('v4', {'file': {'path': 'base.gpkg', 'version': 'v5'}, 'versions': ['v9']}),
    # ('v1', {'file': {'path': 'base.gpkg', 'version': 'v5'}, 'versions': ['v7', 'v6', 'v5', 'v4', 'v3']})  # after remove we can't go any further in history
]


@pytest.mark.parametrize("version,expected", test_history_data)
def test_get_project_with_history(client, diff_project, version, expected):
    resp = client.get(
        "/v1/project/{}/{}?since={}".format(test_workspace_name, test_project, version)
    )
    assert resp.status_code == 200
    history = next(
        item["history"]
        for item in resp.json["files"]
        if item["path"] == expected["file"]["path"]
    )
    assert set(expected["versions"]) == set(history.keys())


def test_get_project_at_version(client, diff_project):
    resp = client.get(f"/v1/project/{test_workspace_name}/{test_project}")
    latest_project = resp.json
    version = "v5"
    resp2 = client.get(
        f"/v1/project/{test_workspace_name}/{test_project}?version={version}"
    )
    info = resp2.json
    # check version non-specific data
    for key in [
        "created",
        "creator",
        "uploads",
        "name",
        "namespace",
        "access",
        "permissions",
    ]:
        assert info[key] == latest_project[key]
    assert info["version"] == version
    version_obj = ProjectVersion.query.filter_by(
        project_id=diff_project.id, name=version
    ).first()
    assert len(info["files"]) == len(version_obj.files)
    assert info["updated"] == version_obj.created.strftime("%Y-%m-%dT%H:%M:%S%zZ")
    assert info["tags"] == ["valid_qgis", "input_use"]
    assert info["disk_usage"] == sum(f["size"] for f in version_obj.files)

    # compare with most recent version
    version = "v10"
    resp3 = client.get(
        f"/v1/project/{test_workspace_name}/{test_project}?version={version}"
    )
    for key, value in latest_project.items():
        # skip updated column as that one would differ slightly due to delay between project and version object update
        if key == "updated" or "latest_version":
            continue
        assert value == resp3.json[key]

    resp4 = client.get(f"/v1/project/{test_workspace_name}/{test_project}?version=v100")
    assert resp4.status_code == 404

    resp5 = client.get(
        f"/v1/project/{test_workspace_name}/{test_project}?version=v1&since=v1"
    )
    assert resp5.status_code == 400


def test_update_project(client):
    project = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()
    # need for private project
    project.access.public = False
    db.session.add(project)
    # add some tester
    test_user = User(
        username="tester", passwd="tester", is_admin=False, email="tester@mergin.com"
    )
    test_user.active = True
    test_user.profile = UserProfile()
    db.session.add(test_user)
    db.session.commit()

    # add tests user as reader to project
    data = {"access": {"readers": project.access.readers + [test_user.id]}}
    resp = client.put(
        "/v1/project/{}/{}".format(test_workspace_name, test_project),
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 200
    assert test_user.id in project.access.readers

    # add tests user as writer to project
    writers = [
        u.username for u in User.query.filter(User.id.in_(project.access.writers)).all()
    ]
    data = {"access": {"writersnames": writers + [test_user.username]}}
    resp = client.put(
        "/v1/project/{}/{}".format(test_workspace_name, test_project),
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 200
    assert test_user.id in project.access.writers

    # try to remove project creator from owners
    data = {"access": {"owners": [test_user.id]}}
    resp = client.put(
        "/v1/project/{}/{}".format(test_workspace_name, test_project),
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 200

    # try to add non-existing user
    readers = [
        user.username
        for user in User.query.filter(User.id.in_(project.access.readers)).all()
    ]
    data = {"access": {"readersnames": readers + ["not-found-user"]}}
    resp = client.put(
        f"/v1/project/{test_workspace_name}/{test_project}",
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 422
    assert resp.json["code"] == "UpdateProjectAccessError"
    assert resp.json["invalid_usernames"] == ["not-found-user"]

    # try to add non-existing user plus make some valid update -> only partial success
    readers = [
        user.username
        for user in User.query.filter(User.id.in_(project.access.readers)).all()
    ]
    data = {
        "access": {
            "readersnames": readers + ["not-found-user"],
            "editorsnames": readers,
            "writersnames": readers,
            "ownersnames": readers,
        }
    }
    resp = client.put(
        f"/v1/project/{test_workspace_name}/{test_project}",
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 207
    assert resp.json["code"] == "UpdateProjectAccessError"

    # login as a new project owner and check permissions
    login(client, test_user.username, "tester")
    resp = client.get(f"/v1/project/{test_workspace_name}/{test_project}")
    assert resp.json["role"] == "owner"


test_download_proj_data = [
    (test_project, None, 200, None),
    (test_project, "zip", 200, None),
    (test_project, "foo", 400, None),
    ("bar", None, 404, None),
    (test_project, None, 200, "v1"),
    (test_project, "zip", 200, "v1"),
    (test_project, "foo", 400, "v1"),
    ("bar", None, 404, "v99"),
    (test_project, None, 404, "v100"),
    (test_project, "zip", 404, "v100"),
    (test_project, "foo", 400, "v100"),
    ("bar", None, 404, "v100"),
]


@pytest.mark.parametrize(
    "proj_name,out_format,expected,version", test_download_proj_data
)
def test_download_project(client, proj_name, out_format, expected, version):
    if out_format:
        resp = client.get(
            "/v1/project/download/{}/{}?{}format={}".format(
                test_workspace_name,
                proj_name,
                "version={}&".format(version) if version else "",
                out_format,
            )
        )
        if expected == 200:
            header = "attachment; filename={}{}.zip".format(
                proj_name, "-" + version if version else ""
            )
            assert header in resp.headers[1][1]
    else:
        resp = client.get(
            "/v1/project/download/{}/{}{}".format(
                test_workspace_name,
                proj_name,
                "?version={}".format(version) if version else "",
            )
        )
        if expected == 200:
            assert "multipart/form-data" in resp.headers[0][1]

    assert resp.status_code == expected


def test_large_project_download_fail(client, diff_project):
    resp = client.get(
        f"/v1/project/download/{test_workspace_name}/{diff_project.name}?v1format=zip"
    )
    assert resp.status_code == 200
    # pretend testing project to be too large by lowering limit
    client.application.config["MAX_DOWNLOAD_ARCHIVE_SIZE"] = 10
    resp = client.get(
        f"/v1/project/download/{test_workspace_name}/{diff_project.name}?v1format=zip"
    )
    assert resp.status_code == 400
    assert "The total size of requested files is too large" in resp.json["detail"]


test_download_file_data = [
    (test_project, "test.txt", "text/plain", 200),
    (test_project, "logo.pdf", "application/pdf", 200),
    (test_project, "logo.jpeg", "image/jpeg", 200),
    (test_project, "base.gpkg", "application/geopackage+sqlite3", 200),
    (test_project, "json.json", "text/plain", 200),
    (test_project, "foo.txt", None, 404),
    ("bar", "test.txt", None, 404),
]


@pytest.mark.parametrize(
    "proj_name,file_path,mimetype,expected", test_download_file_data
)
def test_download_file(client, proj_name, file_path, mimetype, expected):
    resp = client.get(
        "/v1/project/raw/{}/{}?file={}".format(
            test_workspace_name, proj_name, file_path
        )
    )
    assert resp.status_code == expected
    if resp.status_code == 200:
        assert resp.headers["content-type"] == mimetype


test_download_file_version_data = [
    (
        test_project,
        "v9",
        "base.gpkg",
        404,
    ),  # version does not have base.gpkg (but test.gpkg)
    (
        test_project,
        "v7",
        "base.gpkg",
        200,
    ),  # actual changed happened (update with diff)
    (test_project, "v8", "base.gpkg", 200),  # again, file as not changed
    (test_project, "v1", "test.txt", 200),  # initial file (ordinary text file)
    (test_project, "v10", "test.txt", 200),  # unmodified file (ordinary text file)
]


@pytest.mark.parametrize(
    "proj_name,version,file_path,expected", test_download_file_version_data
)
def test_download_file_by_version(
    client, diff_project, proj_name, version, file_path, expected
):
    project = diff_project

    project_version = ProjectVersion.query.filter_by(
        project_id=project.id, name=version
    ).first()
    for file in project_version.files:
        if not is_versioned_file(file["path"]):
            continue

        # let's delete the file, so it can be restored
        if file["path"] == file_path:
            file_location = os.path.join(project.storage.project_dir, file["location"])
            os.remove(file_location)

    # download whole files, no diffs
    resp = client.get(
        "/v1/project/raw/{}/{}?file={}&version={}".format(
            test_workspace_name, proj_name, file_path, version
        )
    )
    assert resp.status_code == expected


test_download_file_diffs_data = [
    (test_project, "", "base.gpkg", 400),  # no version specified
    (test_project, "v3", "base.gpkg", 404),  # upload
    (test_project, "v4", "base.gpkg", 200),  # update with diff
    (test_project, "v5", "base.gpkg", 404),  # forced update without diff
    (test_project, "v10", "test.gpkg", 404),  # nothing changed
    (test_project, "v1", "test.txt", 404),  # ordinary text file
]


@pytest.mark.parametrize(
    "proj_name,version,file_path,expected", test_download_file_diffs_data
)
def test_download_file_version_diffs(
    client, diff_project, proj_name, version, file_path, expected
):
    # download only diffs
    resp = client.get(
        f"/v1/project/raw/{test_workspace_name}/{proj_name}?file={file_path}&version={version}&diff=True"
    )
    assert resp.status_code == expected


def test_download_diff_file(client, diff_project):
    test_file = "base.gpkg"
    # download version of file with force update (no diff)
    resp = client.get(
        "/v1/project/raw/{}/{}?file={}&diff=true&version=v5".format(
            test_workspace_name, test_project, test_file
        )
    )
    assert resp.status_code == 404

    # updated with diff based on 'inserted_1_A.gpkg'
    pv_2 = ProjectVersion.query.filter_by(project_id=diff_project.id, name="v4").first()
    file_meta = pv_2.changes["updated"][0]
    resp = client.get(
        "/v1/project/raw/{}/{}?file={}&diff=true&version=v4".format(
            test_workspace_name, test_project, test_file
        )
    )
    assert resp.status_code == 200
    # check we get the same file with diff that we created (uploaded)
    downloaded_file = os.path.join(TMP_DIR, "download" + str(uuid.uuid4()))
    with open(downloaded_file, "wb") as f:
        f.write(resp.data)
    assert file_meta["diff"]["checksum"] == generate_checksum(downloaded_file)
    patched_file = os.path.join(TMP_DIR, "patched" + str(uuid.uuid4()))
    geodiff = GeoDiff()
    basefile = os.path.join(test_project_dir, test_file)
    shutil.copy(basefile, patched_file)
    geodiff.apply_changeset(patched_file, downloaded_file)
    changes = os.path.join(TMP_DIR, "changeset" + str(uuid.uuid4()))
    geodiff.create_changeset(
        patched_file, os.path.join(test_project_dir, "inserted_1_A.gpkg"), changes
    )
    assert not geodiff.has_changes(changes)

    # download full version after file was removed
    os.remove(os.path.join(diff_project.storage.project_dir, file_meta["location"]))
    resp = client.get(
        "/v1/project/raw/{}/{}?file={}&version=v4".format(
            test_workspace_name, test_project, test_file
        )
    )
    assert resp.status_code == 200

    # try to download full file after file was removed but failed to be restored
    with patch("mergin.sync.storages.disk.DiskStorage.restore_versioned_file") as mock:
        mock.return_value = None
        os.remove(os.path.join(diff_project.storage.project_dir, file_meta["location"]))
        resp = client.get(
            "/v1/project/raw/{}/{}?file={}&version=v4".format(
                test_workspace_name, test_project, test_file
            )
        )
        assert resp.status_code == 404


def test_download_fail(app, client):
    # remove project files to mimic mismatch with db
    os.remove(
        os.path.join(
            app.config["LOCAL_PROJECTS"],
            test_workspace_name,
            test_project,
            "v1",
            "test.txt",
        )
    )
    resp = client.get(
        "/v1/project/raw/{}/{}?file={}".format(
            test_workspace_name, test_project, "test.txt"
        )
    )
    assert resp.status_code == 404

    shutil.rmtree(
        os.path.join(app.config["LOCAL_PROJECTS"], test_workspace_name, test_project)
    )

    resp = client.get(
        "/v1/project/download/{}/{}".format(test_workspace_name, test_project)
    )
    assert resp.status_code == 404

    resp = client.get(
        "/v1/project/raw/{}/{}?file={}".format(
            test_workspace_name, test_project, "test.txt"
        )
    )
    assert resp.status_code == 404

    p = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()
    p.delete()
    db.session.commit()
    resp = client.get(
        "/v1/project/raw/{}/{}?file={}".format(
            test_workspace_name, test_project, "test.txt"
        )
    )
    assert resp.status_code == 404


def create_diff_meta(base, modified, project_dir):
    """Create diff metadata for updating files."""
    geodiff = GeoDiff()
    diff_id = str(uuid.uuid4())
    diff_name = base + "-diff-" + diff_id
    basefile = os.path.join(project_dir, base)
    modfile = os.path.join(project_dir, modified)
    changeset = os.path.join(TMP_DIR, diff_name)
    geodiff.create_changeset(basefile, modfile, changeset)

    diff_meta = {
        **file_info(project_dir, base, chunk_size=CHUNK_SIZE),
        "chunks": [
            str(uuid.uuid4())
            for i in range(
                math.ceil(
                    file_info(TMP_DIR, diff_name, chunk_size=CHUNK_SIZE)["size"]
                    / CHUNK_SIZE
                )
            )
        ],
        "diff": {
            "path": diff_name,
            "checksum": generate_checksum(changeset),
            "size": os.path.getsize(changeset),
        },
    }
    diff_meta["path"] = base
    return diff_meta


def _get_changes(project_dir, diff=False):
    changes = {
        "added": [file_info(project_dir, "test_dir/test4.txt", chunk_size=CHUNK_SIZE)],
        "updated": [file_info(project_dir, "test.txt", chunk_size=CHUNK_SIZE)],
        "removed": [file_info(project_dir, "test3.txt", chunk_size=CHUNK_SIZE)],
    }
    return changes


def _get_changes_without_added(project_dir):
    changes = _get_changes(project_dir)
    changes["added"] = []
    return changes


def _get_changes_without_mtime(project_dir):
    changes = _get_changes_without_added(project_dir)
    del changes["updated"][0]["mtime"]
    return changes


def _get_changes_with_broken_mtime(project_dir):
    changes = _get_changes_without_added(project_dir)
    changes["removed"] = []
    changes["updated"][0]["mtime"] = "frfr"
    return changes


def _get_changes_with_diff(project_dir):
    changes = _get_changes_without_added(project_dir)
    # add some updates using diff file
    diff_meta = create_diff_meta("base.gpkg", "inserted_1_A.gpkg", project_dir)
    changes["updated"].append(diff_meta)
    return changes


def _get_changes_with_diff_0_size(project_dir):
    changes = _get_changes_with_diff(project_dir)
    # tweak file size
    changes["updated"][1]["size"] = 0
    return changes


test_push_data = [
    (
        {"version": "v1", "changes": _get_changes_without_added(test_project_dir)},
        200,
    ),  # success
    (
        {"version": "v1", "changes": _get_changes_with_diff(test_project_dir)},
        200,
    ),  # with diff, success
    (
        {"version": "v1", "changes": _get_changes_with_diff_0_size(test_project_dir)},
        400,
    ),  # broken .gpkg file
    (
        {"version": "v1", "changes": _get_changes(test_project_dir)},
        400,
    ),  # contains already uploaded file
    (
        {"version": "v0", "changes": _get_changes_without_added(test_project_dir)},
        400,
    ),  # version mismatch
    ({"version": "v1", "changes": {}}, 400),  # wrong changes format
    (
        {"version": "v1", "changes": {"added": [], "removed": [], "updated": []}},
        400,
    ),  # no changes requested
    (
        {
            "version": "v1",
            "changes": {
                "added": [{"path": "test.txt"}],
                "removed": [],
                "updated": [{"path": "test.txt"}],
            },
        },
        400,
    ),  # inconsistent changes
    (
        {"changes": _get_changes_without_added(test_project_dir)},
        400,
    ),  # missing version (required parameter)
]


@pytest.mark.parametrize("data,expected", test_push_data)
def test_push_project_start(client, data, expected):
    project = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()
    url = "/v1/project/push/{}/{}".format(test_workspace_name, test_project)
    resp = client.post(
        url,
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    assert resp.status_code == expected
    if expected == 200:
        assert "transaction" in resp.json.keys()
    else:
        failure = SyncFailuresHistory.query.filter_by(project_id=project.id).first()
        # failures are not created when POST request body is invalid (caught by connexion validators)
        if failure:
            assert failure.last_version == "v1"
            assert failure.error_type == "push_start"


def test_push_to_new_project(client):
    # create blank project
    p = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()
    project = Project("blank", p.storage_params, p.creator, p.workspace, files=[])
    db.session.add(project)
    pa = ProjectAccess(project, True)
    db.session.add(pa)
    db.session.commit()

    current_app.config["BLACKLIST"] = ["test4"]
    url = "/v1/project/push/{}/{}".format(test_workspace_name, "blank")
    data = {"version": "v0", "changes": _get_changes(test_project_dir)}
    resp = client.post(
        url,
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    assert resp.status_code == 200

    upload_id = resp.json["transaction"]
    upload = Upload.query.filter_by(id=upload_id).first()
    blacklisted_file = all(
        added["path"] != "test_dir/test4.txt" for added in upload.changes["added"]
    )
    assert blacklisted_file

    data = {"version": "v1", "changes": _get_changes(test_project_dir)}
    resp = client.post(
        url,
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    assert resp.status_code == 400

    data = {"version": "v100", "changes": _get_changes(test_project_dir)}
    resp = client.post(
        url,
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    assert resp.status_code == 400
    assert resp.json["detail"] == "First push should be with v0"
    failure = SyncFailuresHistory.query.filter_by(project_id=project.id).first()
    assert failure.last_version == "v0"
    assert failure.error_type == "push_start"
    assert failure.error_details == "First push should be with v0"


def test_push_integrity_error(client, app):
    app.config["LOCKFILE_EXPIRATION"] = 5
    url = "/v1/project/push/{}/{}".format(test_workspace_name, test_project)
    changes = _get_changes(test_project_dir)
    changes["added"] = changes["removed"] = []
    data = {"version": "v1", "changes": changes}
    resp = client.post(
        url,
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    assert resp.status_code == 200
    project = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()

    # try another request for transaction
    resp2 = client.post(
        url,
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    assert resp2.status_code == 400
    assert resp2.json["detail"] == "Another process is running. Please try later."
    failure = SyncFailuresHistory.query.filter_by(project_id=project.id).first()
    assert failure.error_type == "push_start"
    assert failure.error_details == "Another process is running. Please try later."

    time.sleep(5)
    # try another request for transaction
    resp4 = client.post(
        url,
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    assert resp4.status_code == 200
    # successful push start removes dangling previous attempt (which was not finished/cancelled)
    failure = (
        SyncFailuresHistory.query.filter_by(project_id=project.id)
        .order_by(SyncFailuresHistory.timestamp.desc())
        .first()
    )
    assert failure.error_type == "push_lost"
    assert failure.error_details == "Push artefact removed by subsequent push"

    # try immediate project sync without transaction (no upload)
    changes["added"] = changes["removed"] = changes["updated"] = []
    data = {"version": "v1", "changes": changes}
    resp3 = client.post(
        url,
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    assert resp3.status_code == 400
    failure = (
        SyncFailuresHistory.query.filter_by(project_id=project.id)
        .order_by(SyncFailuresHistory.timestamp.desc())
        .first()
    )
    assert failure.error_type == "push_start"
    assert failure.error_details == "No changes"


def test_exceed_data_limit(client):
    project = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()
    user_disk_space = sum(p.disk_usage for p in project.creator.projects)
    # set basic storage that it is fully used
    Configuration.GLOBAL_STORAGE = user_disk_space

    url = "/v1/project/push/{}/{}".format(test_workspace_name, test_project)
    changes = _get_changes(test_project_dir)
    changes["removed"] = changes["updated"] = []
    changes["added"][0]["path"] = "xxx.txt"
    data = {"version": "v1", "changes": changes}
    resp = client.post(
        url,
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    assert resp.status_code == 422
    assert resp.json["code"] == "StorageLimitHit"
    assert resp.json["detail"] == "You have reached a data limit (StorageLimitHit)"
    assert "current_usage" in resp.json
    assert isinstance(resp.json["storage_limit"], int)
    failure = SyncFailuresHistory.query.filter_by(project_id=project.id).first()
    assert failure.error_type == "push_start"
    assert failure.error_details == "You have reached a data limit (StorageLimitHit)"

    # try to make some space only by removing file
    changes["added"] = []
    changes["removed"] = [project.files[0]]
    data = {"version": "v1", "changes": changes}
    resp = client.post(
        url,
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    assert resp.status_code == 200

    # tight limit again
    Configuration.GLOBAL_STORAGE = sum(p.disk_usage for p in project.creator.projects)
    db.session.commit()

    changes["removed"] = changes["updated"] = []
    changes["added"] = [
        file_info(test_project_dir, "test_dir/test2.txt", chunk_size=CHUNK_SIZE)
    ]
    changes["added"][0]["path"] = "xxx.txt"
    data = {"version": "v2", "changes": changes}
    resp = client.post(
        url,
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    assert resp.status_code == 422
    assert resp.json["detail"] == "You have reached a data limit (StorageLimitHit)"

    # try to upload while removing some other files, test4.txt being larger than test2.txt
    changes["removed"] = [
        file_info(test_project_dir, "test_dir/test4.txt", chunk_size=CHUNK_SIZE)
    ]
    data = {"version": "v2", "changes": changes}
    resp = client.post(
        url,
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    # reset
    Configuration.GLOBAL_STORAGE = 104857600
    assert resp.status_code == 200


def create_transaction(username, changes, version=1):
    """Create transaction in mergin/test project for update to particular version by specified user."""
    user = User.query.filter_by(username=username).first()
    project = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()
    upload = Upload(project, version, changes, user.id)
    db.session.add(upload)
    db.session.commit()
    upload_dir = os.path.join(upload.project.storage.project_dir, "tmp", upload.id)
    os.makedirs(upload_dir)
    open(os.path.join(upload_dir, "lockfile"), "w").close()
    return upload, upload_dir


def remove_transaction(transaction_id):
    """Remove transaction from db and related files, use to clean after upload failure."""
    upload = Upload.query.get(transaction_id)
    upload_dir = os.path.join(upload.project.storage.project_dir, "tmp", transaction_id)
    db.session.delete(upload)
    db.session.commit()
    shutil.rmtree(upload_dir, ignore_errors=True)


def test_chunk_upload(client, app):
    changes = _get_changes(test_project_dir)
    upload, upload_dir = create_transaction("mergin", changes)
    chunk_id = upload.changes["added"][0]["chunks"][0]
    url = "/v1/project/push/chunk/{}/{}".format(upload.id, chunk_id)
    with open(os.path.join(test_project_dir, "test_dir", "test4.txt"), "rb") as file:
        data = file.read(CHUNK_SIZE)
        checksum = hashlib.sha1()
        checksum.update(data)
    headers = {"Content-Type": "application/octet-stream"}
    resp = client.post(url, data=data, headers=headers)
    assert resp.status_code == 200
    assert resp.json["checksum"] == checksum.hexdigest()

    # tests to send bigger chunk than allowed
    app.config["MAX_CHUNK_SIZE"] = 10 * CHUNK_SIZE
    with open(os.path.join(test_project_dir, "test_dir", "test4.txt"), "rb") as file:
        data = file.read(11 * CHUNK_SIZE)
    headers = {"Content-Type": "application/octet-stream"}
    resp = client.post(url, data=data, headers=headers)
    assert resp.status_code == 400
    assert resp.json["detail"] == "Too big chunk"
    failure = SyncFailuresHistory.query.filter_by(project_id=upload.project.id).first()
    assert failure.error_type == "chunk_upload"
    assert failure.error_details == "Too big chunk"

    # tests with transaction with no uploads expected
    changes = _get_changes(test_project_dir)
    changes["added"] = changes["removed"] = changes["updated"] = []
    upload.changes = changes
    db.session.add(upload)
    db.session.commit()
    resp2 = client.post(url, data=data, headers=headers)
    assert resp2.status_code == 404
    assert SyncFailuresHistory.query.count() == 1

    # cleanup
    shutil.rmtree(upload_dir)


def upload_chunks(upload_dir, changes, src_dir=test_project_dir):
    """Mimic chunks for upload to finish were already uploaded."""
    os.makedirs(os.path.join(upload_dir, "chunks"))
    for f in changes["added"] + changes["updated"]:
        source = (
            os.path.join(TMP_DIR, f["diff"]["path"])
            if "diff" in f
            else os.path.join(src_dir, f["path"])
        )
        with open(source, "rb") as in_file:
            for chunk in f["chunks"]:
                with open(os.path.join(upload_dir, "chunks", chunk), "wb") as out_file:
                    out_file.write(in_file.read(CHUNK_SIZE))


def test_push_finish(client):
    changes = _get_changes(test_project_dir)
    upload, upload_dir = create_transaction("mergin", changes)
    url = "/v1/project/push/finish/{}".format(upload.id)

    resp = client.post(url, headers=json_headers)
    assert resp.status_code == 422
    assert "corrupted_files" in resp.json["detail"].keys()
    assert not os.path.exists(os.path.join(upload_dir, "files", "test.txt"))
    failure = SyncFailuresHistory.query.filter_by(project_id=upload.project.id).first()
    assert failure.error_type == "push_finish"
    assert "corrupted_files" in failure.error_details

    os.mkdir(os.path.join(upload.project.storage.project_dir, "v2"))
    # mimic chunks were uploaded
    os.makedirs(os.path.join(upload_dir, "chunks"))
    for f in upload.changes["added"] + upload.changes["updated"]:
        with open(os.path.join(test_project_dir, f["path"]), "rb") as in_file:
            for chunk in f["chunks"]:
                with open(os.path.join(upload_dir, "chunks", chunk), "wb") as out_file:
                    out_file.write(in_file.read(CHUNK_SIZE))

    resp2 = client.post(url, headers={**json_headers, "User-Agent": "Werkzeug"})
    assert resp2.status_code == 200
    assert not os.path.exists(upload_dir)
    version = upload.project.get_latest_version()
    assert version.user_agent
    assert version.device_id == json_headers["X-Device-Id"]
    # chunks is only temporal information, it should not be in db
    assert "chunks" not in version.changes["added"][0].keys()
    assert "chunks" not in version.changes["updated"][0].keys()

    # tests basic failures
    resp3 = client.post("/v1/project/push/finish/not-existing")
    assert resp3.status_code == 404

    # create new user with permission to do uploads
    user = User(
        username="tester", passwd="test", is_admin=False, email="tester@mergin.com"
    )
    user.active = True
    db.session.add(user)
    project = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()
    project.access.owners.append(user.id)
    db.session.commit()

    upload, upload_dir = create_transaction(user.username, changes)
    url = "/v1/project/push/finish/{}".format(upload.id)
    db.session.add(upload)
    db.session.commit()
    # still log in as mergin user
    resp4 = client.post(url)
    assert resp4.status_code == 403

    # other failures with error code 403, 404 does to count to failures history
    assert SyncFailuresHistory.query.count() == 1


def test_push_close(client):
    changes = _get_changes(test_project_dir)
    upload, upload_dir = create_transaction("mergin", changes)
    url = "/v1/project/push/cancel/{}".format(upload.id)
    resp = client.post(url)
    assert resp.status_code == 200


def test_whole_push_process(client):
    """Test whole transactional upload from start, through uploading chunks to finish.
    Uploaded files contains also non-ascii chars to tests.
    """
    test_dir = os.path.join(TMP_DIR, "test_uploaded_files")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    uploaded_files = ["テスト.txt", "£¥§.txt", "name_1_1.txt", "name\\1\\1.txt"]
    # prepare dummy files
    os.mkdir(test_dir)
    for file in uploaded_files:
        with open(os.path.join(test_dir, file), "w") as f:
            f.write("Hello Mergin")

    # push start: create upload transaction
    changes = {
        "added": [
            file_info(test_dir, filename, chunk_size=CHUNK_SIZE)
            for filename in uploaded_files
        ],
        "updated": [],
        "removed": [],
    }
    resp = client.post(
        f"/v1/project/push/{test_workspace_name}/{test_project}",
        data=json.dumps(
            {"version": "v1", "changes": changes}, cls=DateTimeEncoder
        ).encode("utf-8"),
        headers=json_headers,
    )

    assert resp.status_code == 200
    assert "transaction" in resp.json.keys()
    upload = Upload.query.get(resp.json["transaction"])
    assert upload
    # assert we can get project info with active upload
    resp = client.get(f"/v1/project/{test_workspace_name}/{upload.project.name}")
    assert resp.status_code == 200
    assert upload.id in resp.json["uploads"]
    assert (
        client.get(
            f"/v1/project/{test_workspace_name}/{upload.project.name}?version=v1"
        ).status_code
        == 200
    )

    # push upload: upload file chunks
    for file in changes["added"]:
        for chunk_id in file["chunks"]:
            url = "/v1/project/push/chunk/{}/{}".format(upload.id, chunk_id)
            with open(os.path.join(test_dir, file["path"]), "rb") as f:
                data = f.read(CHUNK_SIZE)
                checksum = hashlib.sha1()
                checksum.update(data)
            resp = client.post(
                url, data=data, headers={"Content-Type": "application/octet-stream"}
            )
            assert resp.status_code == 200
            assert resp.json["checksum"] == checksum.hexdigest()

    # push finish: call server to concatenate chunks and finish upload
    resp = client.post(f"/v1/project/push/finish/{upload.id}")
    assert resp.status_code == 200
    project = Project.query.filter_by(
        name=test_project, workspace_id=test_workspace_id
    ).first()
    for file in project.files:
        if file["path"] not in uploaded_files:
            continue
        file_location = os.path.join(project.storage.project_dir, file["location"])
        file_before_upload = os.path.join(test_dir, file["path"])
        assert os.path.exists(file_location)
        assert open(file_before_upload, "r").read() == open(file_location, "r").read()


def test_push_diff_finish(client):
    # success
    changes = _get_changes_with_diff(test_project_dir)
    upload, upload_dir = create_transaction("mergin", changes)
    upload_chunks(upload_dir, upload.changes)
    resp = client.post("/v1/project/push/finish/{}".format(upload.id))
    assert resp.status_code == 200
    # check there are not any changes between local modified file and server patched file (using geodiff)
    geodiff = GeoDiff()
    changeset = os.path.join(TMP_DIR, "test_changeset")
    modfile = os.path.join(test_project_dir, "inserted_1_A.gpkg")
    patchedfile = os.path.join(upload.project.storage.project_dir, "v2", "base.gpkg")
    geodiff.create_changeset(patchedfile, modfile, changeset)
    assert not geodiff.has_changes(changeset)
    os.remove(changeset)
    # check we track performance of reconstruction
    gh = GeodiffActionHistory.query.filter_by(
        project_id=upload.project.id, base_version="v1", target_version="v2"
    ).first()
    assert gh.geodiff_time
    assert gh.copy_time
    assert gh.checksum_time
    assert gh.action == "apply_changes"

    # try with valid update metadata but with conflicting diff (rebase was not done)
    upload, upload_dir = create_transaction("mergin", changes, 2)
    upload_chunks(upload_dir, upload.changes)

    resp = client.post("/v1/project/push/finish/{}".format(upload.id))
    assert resp.status_code == 422
    assert (
        "GEODIFF ERROR: Nothing inserted (this should never happen)"
        in resp.json["detail"]
    )
    error = resp.json["detail"]

    # try again to make sure geodiff logs are related only to recent event
    client.post("/v1/project/push/cancel/{}".format(upload.id))
    upload, upload_dir = create_transaction("mergin", changes, 2)
    upload_chunks(upload_dir, upload.changes)
    resp = client.post("/v1/project/push/finish/{}".format(upload.id))
    assert resp.status_code == 422
    assert resp.json["detail"] == error

    # fail if diff file is not valid
    changes = _get_changes_with_diff_0_size(test_project_dir)
    upload, upload_dir = create_transaction("mergin", changes, 3)
    upload_chunks(upload_dir, upload.changes)
    resp = client.post("/v1/project/push/finish/{}".format(upload.id))
    assert resp.status_code == 422


def test_push_no_diff_finish(client):
    working_dir = os.path.join(TMP_DIR, "test_push_no_diff_finish")
    # cleanup
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)

    shutil.copytree(test_project_dir, working_dir)
    # mimic base.gpkg was updated with inserted_1_A.gpkg (but no diff is created)
    shutil.copy(
        os.path.join(working_dir, "inserted_1_A.gpkg"),
        os.path.join(working_dir, "base.gpkg"),
    )
    changes = {
        "added": [],
        "removed": [],
        "updated": [file_info(working_dir, "base.gpkg", chunk_size=CHUNK_SIZE)],
    }
    upload, upload_dir = create_transaction("mergin", changes)
    upload_chunks(upload_dir, upload.changes, src_dir=working_dir)
    resp = client.post("/v1/project/push/finish/{}".format(upload.id))
    assert resp.status_code == 200
    # check diff file was generated by server, and it is in file history
    latest_version = upload.project.get_latest_version()
    file_meta = latest_version.changes["updated"][0]
    assert "diff" in file_meta
    assert os.path.exists(
        os.path.join(upload.project.storage.project_dir, file_meta["diff"]["location"])
    )

    # change structure of gpkg file so diff would not be available -> hard overwrite
    gpkg_conn = pysqlite3.connect(os.path.join(working_dir, "base.gpkg"))
    gpkg_conn.enable_load_extension(True)
    gpkg_cur = gpkg_conn.cursor()
    gpkg_cur.execute('SELECT load_extension("mod_spatialite")')
    gpkg_cur.execute("ALTER TABLE simple ADD COLUMN new_col")
    gpkg_conn.commit()
    changes = {
        "added": [],
        "removed": [],
        "updated": [file_info(working_dir, "base.gpkg", chunk_size=CHUNK_SIZE)],
    }
    upload, upload_dir = create_transaction("mergin", changes, version=2)
    upload_chunks(upload_dir, upload.changes, src_dir=working_dir)
    resp = client.post("/v1/project/push/finish/{}".format(upload.id))
    assert resp.status_code == 200
    # check diff file was generated by server, and it is in file history
    latest_version = upload.project.get_latest_version()
    file_meta = latest_version.changes["updated"][0]
    assert "diff" not in file_meta
    version_files = os.listdir(os.path.join(upload.project.storage.project_dir, "v3"))
    diff_files = [f for f in version_files if re.findall("-diff-", f)]
    assert not diff_files


clone_project_data = [
    ({"project": " clone "}, "mergin", 200),  # clone own project
    (
        {"project": " clone.new "},
        "mergin",
        200,
    ),  # clone project with dot in the middle of project name
    ({"project": " clone/new"}, "mergin", 400),  # try to clone project with slash char
    (
        {"project": " .clone"},
        "mergin",
        400,
    ),  # try to clone project with dot on start of the project name
    (
        {"project": " support"},
        "mergin",
        400,
    ),  # try to clone project with forbidden project name
    ({"project": ""}, "mergin", 400),  # try to clone project without name
    ({"project": "  "}, "mergin", 400),  # try to clone project without name
    ({}, "mergin", 409),  # fail to clone own project into the same one
    ({"project": "foo_clone"}, "foo", 200),  # public project cloned by another user
    (
        {"project": "foo_clone", "namespace": "foo"},
        "foo",
        404,
    ),  # project cloned to non-existing namespace
    ({"project": "storage_limit_hit"}, "mergin", 422),  # StorageLimitHit
]


@pytest.mark.parametrize("data,username,expected", clone_project_data)
def test_clone_project(client, data, username, expected):
    # create new version with diff
    upload, upload_dir = create_transaction(
        "mergin", _get_changes_with_diff(test_project_dir)
    )
    upload_chunks(upload_dir, upload.changes)
    resp = client.post("/v1/project/push/finish/{}".format(upload.id))
    assert resp.status_code == 200

    endpoint = "/v1/project/clone/{}/{}".format(test_workspace_name, test_project)
    # add some user to tests clone across namespaces
    if username != "mergin":
        user = add_user(username, "bar")
        # allow user to write into workspace, e.g. create project
        Configuration.GLOBAL_ADMIN = True
        # switch default user
        client.get(url_for("/.mergin_auth_controller_logout"))
        client.post(
            url_for("/.mergin_auth_controller_login"),
            data=json.dumps({"login": user.username, "password": "bar"}),
            headers=json_headers,
        )
    # abort when there is not enough storage
    if "project" in data and data["project"] == "storage_limit_hit":
        project = Project.query.filter_by(
            name=test_project, workspace_id=test_workspace_id
        ).first()
        user_disk_space = sum(p.disk_usage for p in project.creator.projects)
        # set basic storage that it is fully used
        Configuration.GLOBAL_STORAGE = user_disk_space
    resp = client.post(endpoint, data=json.dumps(data), headers=json_headers)
    assert resp.status_code == expected
    if expected == 422:
        assert resp.json["code"] == "StorageLimitHit"
        assert resp.json["detail"] == "You have reached a data limit (StorageLimitHit)"
    if expected == 200:
        proj = data.get("project", test_project).strip()
        template = Project.query.filter_by(
            name=test_project, workspace_id=test_workspace_id
        ).first()
        project = Project.query.filter_by(
            name=proj, workspace_id=test_workspace_id
        ).first()
        assert not any(
            x["checksum"] != y["checksum"] and x["path"] != y["path"]
            for x, y in zip(project.files, template.files)
        )
        assert os.path.exists(
            os.path.join(project.storage.project_dir, project.files[0]["location"])
        )
        assert not project.access.public
        # check if there is no diffs in cloned files
        assert not any("diff" in file for file in project.files)
        pv = project.get_latest_version()
        assert not any("diff" in file for file in pv.files)
        assert pv.changes.get("removed") == []
        assert pv.changes.get("updated") == []
        assert pv.device_id == json_headers["X-Device-Id"]
        assert "diff" not in pv.changes.get("added")
        # cleanup
        shutil.rmtree(project.storage.project_dir)


def test_optimize_storage(app, client, diff_project):
    from ..sync.tasks import optimize_storage

    # rename test.gpkg to base.gpkg to mimic file was overwritten rather than "renamed" in v9
    pv = (
        ProjectVersion.query.filter(ProjectVersion.project == diff_project)
        .filter_by(name="v9")
        .first()
    )
    del pv.changes["removed"][0]
    del pv.changes["added"][0]
    file_v9_base = os.path.join(diff_project.storage.project_dir, "v9", "base.gpkg")
    os.rename(
        os.path.join(diff_project.storage.project_dir, "v9", "test.gpkg"), file_v9_base
    )
    pv.changes["updated"] = [
        file_info(test_project_dir, "base.gpkg", chunk_size=CHUNK_SIZE)
    ]
    ver_file = next(f for f in pv.files if f["path"] == "test.gpkg")
    ver_file["path"] = "base.gpkg"
    proj_file = next(f for f in diff_project.files if f["path"] == "test.gpkg")
    proj_file["path"] = "base.gpkg"
    flag_modified(diff_project, "files")
    flag_modified(pv, "changes")
    db.session.commit()

    file_v2_base = os.path.join(diff_project.storage.project_dir, "v4", "base.gpkg")
    file_v4_base = os.path.join(diff_project.storage.project_dir, "v6", "base.gpkg")
    basefile_v1 = os.path.join(diff_project.storage.project_dir, "v3", "base.gpkg")
    basefile_v3 = os.path.join(diff_project.storage.project_dir, "v5", "base.gpkg")
    latest = os.path.join(diff_project.storage.project_dir, "v9", "base.gpkg")

    # backup some file to restore it later
    backup = os.path.join(tempfile.gettempdir(), "base.gpkg")
    shutil.copy(file_v2_base, backup)

    # make sure we start with project on version v10
    assert diff_project.latest_version == "v10"

    optimize_storage(diff_project.id)
    # nothing removed since the latest version in not
    assert os.path.exists(file_v2_base) and os.path.exists(file_v4_base)

    # nothing removed since created recently
    assert os.path.exists(file_v2_base) and os.path.exists(file_v4_base)

    # remove constraint on file age
    SyncConfiguration.FILE_EXPIRATION = 0
    optimize_storage(diff_project.id)
    assert not (os.path.exists(file_v2_base) and os.path.exists(file_v4_base))
    # we keep latest file, basefiles must stay (either very first one, or any other with forced update)
    assert (
        os.path.exists(latest)
        and os.path.exists(basefile_v1)
        and os.path.exists(basefile_v3)
    )

    # try again, nothing expected if files already removed
    optimize_storage(diff_project.id)
    assert not os.path.exists(file_v2_base)

    # restore file, create new version v11 to mimic that optimize function is not called on push
    shutil.copy(backup, file_v2_base)
    changes = _get_changes(test_project_dir)
    upload, upload_dir = create_transaction("mergin", changes, version=11)
    # mimic chunks were uploaded
    os.makedirs(os.path.join(upload_dir, "chunks"))
    for f in upload.changes["added"] + upload.changes["updated"]:
        with open(os.path.join(test_project_dir, f["path"]), "rb") as in_file:
            for chunk in f["chunks"]:
                with open(os.path.join(upload_dir, "chunks", chunk), "wb") as out_file:
                    out_file.write(in_file.read(CHUNK_SIZE))

    resp = client.post(f"/v1/project/push/finish/{upload.id}")
    assert resp.status_code == 200
    assert os.path.exists(file_v2_base)


def test_file_diffs_chain(diff_project):
    # file test.gpkg was added only in v9, and then left intact
    # direct search
    basefile, diffs = diff_project.file_diffs_chain("test.gpkg", "v2")
    assert not basefile
    assert not diffs
    # reverse search
    basefile, diffs = diff_project.file_diffs_chain("test.gpkg", "v8")
    assert not basefile
    assert not diffs

    # ask for basefile
    basefile, diffs = diff_project.file_diffs_chain("test.gpkg", "v9")
    assert basefile["version"] == "v9"
    assert basefile["change"] == "added"
    assert not diffs

    # version history has been broken by removal of file in v2
    basefile, diffs = diff_project.file_diffs_chain("base.gpkg", "v2")
    assert not basefile
    assert not diffs

    # file was re-added in v3
    basefile, diffs = diff_project.file_diffs_chain("base.gpkg", "v3")
    assert basefile["version"] == "v3"
    assert basefile["change"] == "added"
    assert not diffs

    # diff was used in v4, direct search
    basefile, diffs = diff_project.file_diffs_chain("base.gpkg", "v4")
    assert basefile["version"] == "v3"
    assert len(diffs) == 1
    assert "v4" in diffs[0]["location"]

    # file was overwritten in v5
    basefile, diffs = diff_project.file_diffs_chain("base.gpkg", "v5")
    assert basefile["version"] == "v5"
    assert basefile["change"] == "updated"
    assert not diffs

    # diff was used in v6, reverse search followed by direct search
    basefile, diffs = diff_project.file_diffs_chain("base.gpkg", "v6")
    assert basefile["version"] == "v5"
    assert len(diffs) == 1
    assert "v6" in diffs[0]["location"]

    # diff was used in v7, nothing happened in v8 (=v7), reverse search followed by direct search
    basefile, diffs = diff_project.file_diffs_chain("base.gpkg", "v8")
    assert basefile["version"] == "v5"
    assert len(diffs) == 2

    # file was removed in v9
    basefile, diffs = diff_project.file_diffs_chain("base.gpkg", "v9")
    assert not basefile
    assert not diffs

    # ask for latest version, but file is already gone
    basefile, diffs = diff_project.file_diffs_chain("base.gpkg", "v10")
    assert not basefile
    assert not diffs

    # remove v9 and v10 to mimic that project history end with existing file
    pv_8 = ProjectVersion.query.filter_by(project_id=diff_project.id, name="v8").first()
    pv_9 = ProjectVersion.query.filter_by(project_id=diff_project.id, name="v9").first()
    pv_10 = ProjectVersion.query.filter_by(
        project_id=diff_project.id, name="v10"
    ).first()
    diff_project.latest_version = "v8"
    diff_project.files = pv_8.files
    flag_modified(diff_project, "files")
    db.session.delete(pv_9)
    db.session.delete(pv_10)
    db.session.commit()

    # diff was used in v6, v7, nothing happened in v8 => v7 = v8, reverse search
    basefile, diffs = diff_project.file_diffs_chain("base.gpkg", "v6")
    assert basefile["version"] == "v7"
    assert len(diffs) == 1
    assert "v7" in diffs[0]["location"]

    # we asked for last existing file version - basefile
    basefile, diffs = diff_project.file_diffs_chain("base.gpkg", "v7")
    assert basefile["version"] == "v7"
    assert not diffs

    # we asked for last project version
    basefile, diffs = diff_project.file_diffs_chain("base.gpkg", "v8")
    assert basefile["version"] == "v7"
    assert not diffs


changeset_data = [
    ("v1", "test.gpkg", 404),
    ("v1", "test.txt", 404),
    ("v7", "base.gpkg", 200),  # diff update in v7 version
    ("v8", "base.gpkg", 404),  # no change of the file in v8 version
]


@pytest.mark.parametrize("version, path, expected", changeset_data)
def test_changeset_file(client, diff_project, version, path, expected):
    pv = ProjectVersion.query.filter_by(
        project_id=diff_project.id, name=version
    ).first()

    url = "/v1/resource/changesets/{}/{}/{}?path={}".format(
        test_workspace_name, test_project, version, path
    )
    resp = client.get(url)
    assert resp.status_code == expected

    if expected == 200 and is_versioned_file(path):
        # remove gpkg file, so it is reconstructed on demand and request still works
        f = pv.project.storage.file_path(os.path.join(version, path))
        if os.path.exists(f):
            os.remove(f)
        assert client.get(url).status_code == 200

    if resp.status_code == 200:
        file = next((f for f in pv.files if f["path"] == path), None)
        changeset = os.path.join(
            pv.project.storage.project_dir, file["diff"]["location"]
        )
        json_file = "changeset"

        # create manually list changes
        pv.project.storage.geodiff.list_changes(changeset, json_file)
        list_changes = json.loads(open(json_file, "r").read())
        os.remove(json_file)

        # compare manually created with data from request
        resp_data = json.loads(resp.data)[0]
        assert resp_data["table"] == list_changes["geodiff"][0]["table"]
        assert resp_data["type"] == list_changes["geodiff"][0]["type"]
        assert "name" in resp_data["changes"][0]
        assert "type" in resp_data["changes"][0]
        assert len(resp_data["changes"]) == len(
            list_changes["geodiff"][0]["changes"]
        )  # do not compare content to avoid wkt vs wkb mismatch


def test_get_projects_by_uuids(client):
    user = User.query.filter_by(username="mergin").first()
    test_workspace = create_workspace()
    p1 = create_project("foo", test_workspace, user)
    user2 = add_user("user2", "ilovemergin")
    test_workspace_2 = create_workspace()
    test_workspace_2._id = (
        2  # FIXME: This should be refactored due to only one workspace in CE
    )
    p2 = create_project("foo", test_workspace_2, user2)
    uuids = ",".join([str(p1.id), str(p2.id), "1234"])

    resp = client.get(f"/v1/project/by_uuids?uuids={uuids}")
    assert resp.status_code == 200
    assert str(p1.id) in resp.json  # user has access to
    assert (
        str(p2.id) not in resp.json
    )  # belongs to user2, and user does not have access
    assert "1234" not in resp.json  # invalid id

    uuids = ",".join([str(uuid.uuid4()) for _ in range(0, 11)])
    resp = client.get(f"/v1/project/by_uuids?uuids={uuids}")
    assert resp.status_code == 400

    resp = client.get(f"/v1/project/by_uuids")
    assert resp.status_code == 400


def test_get_paginated_versions(client, diff_project):
    resp = client.get(
        "/v1/project/versions/paginated/{}/{}?page={}&per_page={}".format(
            test_workspace_name, test_project, 1, 5
        )
    )
    assert resp.status_code == 200
    result = json.loads(resp.data)
    assert result.get("count") == 10
    assert len(result.get("versions")) == 5
    assert result.get("versions")[0].get("name") == "v10"

    resp = client.get(
        "/v1/project/versions/paginated/{}/{}?page={}&per_page={}".format(
            test_workspace_name, test_project, 2, 5
        )
    )
    assert resp.status_code == 200
    result = json.loads(resp.data)
    assert result.get("count") == 10
    assert len(result.get("versions")) == 5
    assert result.get("versions")[0].get("name") == "v5"

    resp = client.get(
        "/v1/project/versions/paginated/{}/{}?page={}&per_page={}&descending=false".format(
            test_workspace_name, test_project, 1, 5
        )
    )
    assert resp.status_code == 200
    result = json.loads(resp.data)
    assert result.get("count") == 10
    assert len(result.get("versions")) == 5
    assert result.get("versions")[0].get("name") == "v1"


conflict_files = [
    "test.gpkg_conflict_copy",
    "test.qgs_conflict_copy",
    "test.qgz_conflict_copy",
    "test.gpkg_rebase_conflicts",
    "data (conflicted copy, mergin v5).gpkg",
    "data (edit conflict, mergin v5).json",
]


@pytest.mark.parametrize("file", conflict_files)
def test_project_conflict_files(diff_project, file):
    ws_ids = [diff_project.workspace_id]
    workspaces_map = {w.id: w.name for w in current_app.ws_handler.get_by_ids(ws_ids)}
    ctx = {"workspaces_map": workspaces_map}
    project_info = ProjectListSchema(only=("has_conflict",), context=ctx).dump(
        diff_project
    )
    assert not project_info["has_conflict"]

    # tests if project contains conflict files
    files = diff_project.files.copy()
    files.append(
        {
            "checksum": "89469a6482267de394c7c7270cb7ffafe694ea76",
            "mtime": "2021-04-14T17:33:32.766731Z",
            "path": file,
            "size": 98304,
        }
    )
    diff_project.files = files
    flag_modified(diff_project, "files")
    db.session.commit()

    project_info = ProjectListSchema(only=("has_conflict",), context=ctx).dump(
        diff_project
    )
    assert project_info["has_conflict"]


def test_orphan_project(client):
    """Test project whose creator was removed"""
    user = add_user("tests", "tests")
    user_id = user.id
    test_workspace = create_workspace()
    project = create_project("orphan", test_workspace, user)
    assert project.creator_id == user_id
    assert project.access.owners == [user_id]

    # user is removed by superuser
    login_as_admin(client)
    resp = client.delete(
        url_for("/.mergin_auth_controller_delete_user", username=user.username)
    )
    assert resp.status_code == 204
    assert User.query.filter_by(id=user_id).count()
    assert user.username.startswith("deleted_") and not user.active
    # project still exists (it belongs to workspace)
    p = Project.query.filter_by(name="orphan").first()
    assert p.creator_id
    assert p.access.owners == []

    # superuser as workspace owner has access to project and can assign new writer/owner
    resp = client.get(f"/v1/project/{test_workspace.name}/{p.name}")
    assert resp.json["creator"] == p.creator_id
    assert resp.json["access"]["owners"] == []
    assert resp.json["role"] == "owner"

    admin = User.query.filter_by(username="mergin").first()
    data = {"access": {"readers": [admin.id], "writers": [admin.id], "public": True}}
    resp = client.put(
        f"/v1/project/{test_workspace.name}/{p.name}",
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 200
    resp = client.get(f"/v1/project/{test_workspace.name}/{p.name}")
    assert resp.json["access"]["writers"] == [admin.id]
    assert resp.json["access"]["public"]

    data = {
        "access": {
            "ownersnames": [admin.username],
        }
    }
    assert (
        client.put(
            f"/v1/project/{test_workspace.name}/{p.name}",
            data=json.dumps(data),
            headers=json_headers,
        ).status_code
        == 200
    )
    resp = client.get(f"/v1/project/{test_workspace.name}/{p.name}")
    assert resp.json["creator"]
    assert resp.json["access"]["owners"] == [admin.id]

    # project will however not be listed as 'created' projects
    created_projects = Project.query.filter(Project.creator_id == admin.id)
    assert not next((p for p in created_projects if p.name == "orphan"), None)


def test_inactive_project(client, diff_project):
    """Project set for removal is not listed and can not be updated"""
    user = add_user("tests", "tests")
    diff_project.access.set_role(user.id, ProjectRole.OWNER)
    diff_project.removed_at = datetime.datetime.utcnow()
    db.session.commit()
    project_path = get_project_path(diff_project)

    # get/list/access project
    login(client, "tests", "tests")
    resp = client.get("/v1/project/paginated?page=1&per_page=10")
    assert diff_project.name not in [p["name"] for p in resp.json["projects"]]

    data = {"projects": [project_path]}
    resp = client.post(
        "/v1/project/by_names", data=json.dumps(data), headers=json_headers
    )
    assert resp.json.get(project_path).get("error") == 404

    resp = client.get(f"/v1/project/by_uuids?uuids={diff_project.id}")
    assert resp.json == {}

    resp = client.get(f"/v1/project/{project_path}?since=v1")
    assert resp.status_code == 404

    resp = client.get(f"/v1/project/{project_path}")
    assert resp.status_code == 404

    resp = client.get(f"/v1/project/download/{project_path}?v1format=zip")
    assert resp.status_code == 404

    assert "test.txt" in [f["path"] for f in diff_project.files]
    resp = client.get(f"/v1/project/raw/{project_path}?file=test.txt")
    assert resp.status_code == 404

    data = {"project": "clone"}
    resp = client.post(
        f"/v1/project/clone/{project_path}", data=json.dumps(data), headers=json_headers
    )
    assert resp.status_code == 404

    # modify project
    data = {"access": {"readers": diff_project.access.readers + [user.id]}}
    resp = client.put(
        f"/v1/project/{project_path}", data=json.dumps(data), headers=json_headers
    )
    assert resp.status_code == 404

    # push - start transaction, push to existing transaction, finish/cancel transaction
    data = {"version": "v1", "changes": _get_changes_without_added(test_project_dir)}
    resp = client.post(
        f"/v1/project/push/{project_path}",
        data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
        headers=json_headers,
    )
    assert resp.status_code == 404

    upload, upload_dir = create_transaction("mergin", _get_changes(test_project_dir))
    chunk_id = upload.changes["added"][0]["chunks"][0]
    resp = client.post(
        f"/v1/project/push/chunk/{upload.id}/{chunk_id}",
        data=data,
        headers={"Content-Type": "application/octet-stream"},
    )
    assert resp.status_code == 404

    resp = client.post(f"/v1/project/push/finish/{upload.id}")
    assert resp.status_code == 404

    resp = client.post(f"/v1/project/push/cancel/{upload.id}")
    assert resp.status_code == 404

    # delete project again
    resp = client.delete(f"/v1/project/{project_path}")
    assert resp.status_code == 404

    # create project with the same name
    Configuration.GLOBAL_ADMIN = True
    data = {"name": diff_project.name}
    resp = client.post(
        f"/v1/project/{diff_project.workspace.name}",
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 409
    assert (
        "Project with the same name is scheduled for deletion, "
        "you can create a project with this name in "
        + str(client.application.config["DELETED_PROJECT_EXPIRATION"])
        + " days"
        in resp.json["detail"]
    )

    # clone with the name of inactive project
    p = create_project("proj_to_clone", diff_project.workspace, user)
    data = {"project": diff_project.name}
    resp = client.post(
        f"/v1/project/clone/{diff_project.workspace.name}/{p.name}",
        data=json.dumps(data),
        headers=json_headers,
    )
    assert resp.status_code == 409
    assert (
        "Project with the same name is scheduled for deletion, "
        "you can create a project with this name in "
        + str(client.application.config["DELETED_PROJECT_EXPIRATION"])
        + " days"
        in resp.json["detail"]
    )


def test_get_project_version(client, diff_project):
    # success - latest version
    resp = client.get(
        f"/v1/project/version/{str(diff_project.id)}/{diff_project.latest_version}"
    )
    assert resp.status_code == 200
    assert resp.json["name"] == diff_project.latest_version

    # success any older version
    resp = client.get(f"/v1/project/version/{str(diff_project.id)}/v1")
    assert resp.status_code == 200
    assert resp.json["name"] == "v1"

    # not existing version
    resp = client.get(f"/v1/project/version/{str(diff_project.id)}/v100")
    assert resp.status_code == 404

    # invalid version identifier
    resp = client.get(f"/v1/project/version/{str(diff_project.id)}/500")
    assert resp.status_code == 404

    # invalid project identifier
    resp = client.get(f"/v1/project/version/1234/v10")
    assert resp.status_code == 404


def add_project_version(project, changes, version=2):
    pv = ProjectVersion(
        project,
        f"v{version}",
        "mergin",
        changes,
        project.files,
        "123",
    )
    db.session.add(pv)
    db.session.commit()
    return pv


def test_project_version_integrity(client):
    # changes with an upload
    # create transaction and upload chunks
    changes = _get_changes_with_diff(test_project_dir)
    upload, upload_dir = create_transaction("mergin", changes)
    upload_chunks(upload_dir, upload.changes)
    # manually create an identical project version in db
    next_version = "v{}".format(upload.version + 1)
    pv = ProjectVersion(
        upload.project,
        next_version,
        "mergin",
        changes,
        upload.project.files,
        "123",
    )
    db.session.add(pv)
    db.session.commit()
    # try to finish the transaction
    resp = client.post("/v1/project/push/finish/{}".format(upload.id))
    assert resp.status_code == 422
    assert "Failed to create new version" in resp.json["detail"]
    failure = SyncFailuresHistory.query.filter_by(project_id=upload.project.id).first()
    assert failure.error_type == "push_finish"
    assert "Failed to create new version" in failure.error_details
    db.session.delete(pv)
    db.session.delete(failure)
    db.session.commit()

    # changes without an upload
    # to insert an identical project version when no upload (only one endpoint used),
    # we need to pretend side effect of a function called just before project version insertion
    with patch("mergin.sync.utils.get_user_agent") as mock:
        project = Project.query.filter_by(
            name=test_project, workspace_id=test_workspace_id
        ).first()
        url = "/v1/project/push/{}/{}".format(test_workspace_name, test_project)
        changes = _get_changes(test_project_dir)
        changes["added"] = changes["updated"] = []  # only deleted files
        data = {"version": "v1", "changes": changes}
        pv = mock.side_effect = add_project_version(project, changes)
        resp = client.post(
            url,
            data=json.dumps(data, cls=DateTimeEncoder).encode("utf-8"),
            headers=json_headers,
        )
        assert resp.status_code == 422
        assert "Failed to upload a new project version" in resp.json["detail"]
        failure = SyncFailuresHistory.query.filter_by(
            project_id=upload.project.id
        ).first()
        assert failure.error_type == "push_start"
        assert "Failed to upload a new project version" in failure.error_details
        db.session.delete(pv)
        db.session.commit()

    # check infrastructure is clean for successful push if no version conflict occur
    changes = _get_changes(test_project_dir)
    upload, upload_dir = create_transaction("mergin", changes)
    upload_chunks(upload_dir, upload.changes)
    resp = client.post("/v1/project/push/finish/{}".format(upload.id))
    assert resp.status_code == 200
