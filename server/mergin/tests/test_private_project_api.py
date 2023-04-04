# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial

import datetime
import json
import os

from flask import url_for

from .. import db
from ..sync.models import AccessRequest, Project, ProjectRole
from ..auth.models import User
from ..config import Configuration
from . import json_headers
from .utils import add_user, login, create_project, create_workspace


def test_project_unsubscribe(client, diff_project):
    # create user and grant him write access
    user = add_user("reader", "reader")
    diff_project.access.set_role(user.id, ProjectRole.WRITER)
    db.session.commit()

    # project owner is logged in
    resp = client.post(
        url_for(
            "/app.mergin_sync_private_api_controller_unsubscribe_project",
            id=diff_project.id,
        )
    )
    assert resp.status_code == 400
    assert resp.json.get("detail") == "Owner cannot leave a project"

    login(client, "reader", "reader")
    # reader is logged in
    resp = client.post(
        url_for(
            "/app.mergin_sync_private_api_controller_unsubscribe_project",
            id=diff_project.id,
        )
    )
    assert resp.status_code == 200
    assert not diff_project.access.get_role(user.id)
    assert user.id not in diff_project.access.readers
    assert user.id not in diff_project.access.writers


def test_project_access_request(client):
    """Test project access CRUD operations"""
    user = User.query.filter(User.username == "mergin").first()
    test_workspace = create_workspace()
    p = create_project("testx", test_workspace, user)
    user2 = add_user("test_user", "ilovemergin")
    login(client, "test_user", "ilovemergin")
    resp = client.post(
        f"/app/project/access-request/{test_workspace.name}/{p.name}",
        headers=json_headers,
    )
    access_request = AccessRequest.query.filter(
        AccessRequest.project_id == p.id
    ).first()
    assert resp.status_code == 200
    assert access_request.user.username == "test_user"

    # already exists
    resp = client.post(
        f"/app/project/access-request/{test_workspace.name}/{p.name}",
        headers=json_headers,
    )
    assert resp.status_code == 409

    # user can check outgoing access requests
    resp = client.get("/app/project/access-requests")
    assert resp.status_code == 200
    resp_data = json.loads(resp.data)
    assert resp_data[0]["requested_by"] == "test_user"

    # remove access request
    resp = client.delete(
        f"/app/project/access-request/{access_request.id}", headers=json_headers
    )
    assert resp.status_code == 200
    assert not AccessRequest.query.filter(AccessRequest.project_id == p.id).first()

    # recreate request again
    resp = client.post(
        f"/app/project/access-request/{test_workspace.name}/{p.name}",
        headers=json_headers,
    )
    assert resp.status_code == 200
    access_request = AccessRequest.query.filter(
        AccessRequest.project_id == p.id
    ).first()
    assert access_request.user.username == "test_user"

    # user can not list incoming namespace access requests
    Configuration.GLOBAL_ADMIN = False
    assert (
        client.get(
            f"/app/project/access-request/{test_workspace.name}?page=1&per_page=10", headers=json_headers
        ).status_code
        == 403
    )

    # user can not accept its own access request
    data = {"permissions": "write"}
    resp = client.post(
        f"/app/project/access-request/accept/{access_request.id}",
        headers=json_headers,
        data=json.dumps(data),
    )
    assert resp.status_code == 403

    # login as workspace admin to list incoming request and accept it
    login(client, "mergin", "ilovemergin")
    resp = client.get(
        f"/app/project/access-request/{test_workspace.name}?page=1&per_page=10", headers=json_headers
    )
    assert resp.status_code == 200
    access_requests = resp.json.get("access_requests")
    assert access_requests[0]["requested_by"] == "test_user"
    assert access_requests[0]["namespace"] == test_workspace.name

    resp = client.post(
        f"/app/project/access-request/accept/{access_request.id}",
        headers=json_headers,
        data=json.dumps(data),
    )
    assert resp.status_code == 200
    assert not AccessRequest.query.filter(AccessRequest.project_id == p.id).first()
    project = Project.query.filter(
        Project.name == "testx", Project.workspace_id == test_workspace.id
    ).first()
    assert user2.id in project.access.readers
    assert user2.id in project.access.writers
    assert user2.id not in project.access.owners

    # try to create access request again - user was already granted access
    login(client, "test_user", "ilovemergin")
    resp = client.post(
        f"/app/project/access-request/{test_workspace.name}/{p.name}",
        headers=json_headers,
    )
    assert resp.status_code == 409

    # try with inactive project
    rp = create_project("removed_project", test_workspace, user)
    rp.removed_at = datetime.datetime.utcnow()
    db.session.commit()

    resp = client.post(
        f"/app/project/access-request/{test_workspace.name}/{rp.name}",
        headers=json_headers,
    )
    assert resp.status_code == 404

    # pretend request was already created before project was removed
    rp.removed_at = None
    db.session.commit()
    resp = client.post(
        f"/app/project/access-request/{test_workspace.name}/{rp.name}",
        headers=json_headers,
    )
    assert resp.status_code == 200
    rp.removed_at = datetime.datetime.utcnow()
    db.session.commit()
    access_request = AccessRequest.query.filter(
        AccessRequest.project_id == rp.id
    ).first()

    resp = client.get("/app/project/access-requests")
    assert resp.status_code == 200
    assert len(resp.json) == 0

    resp = client.delete(
        f"/app/project/access-request/{access_request.id}", headers=json_headers
    )
    assert resp.status_code == 404

    login(client, "mergin", "ilovemergin")
    resp = client.get(
        f"/app/project/access-request/{test_workspace.name}?page=1&per_page=10", headers=json_headers
    )
    assert resp.status_code == 200
    assert resp.json.get("count") == 0

    data = {"permissions": "write"}
    resp = client.post(
        f"/app/project/access-request/accept/{access_request.id}",
        headers=json_headers,
        data=json.dumps(data),
    )
    assert resp.status_code == 404


def test_list_namespace_project_access_requests(client):
    """Test project access requests pagination"""
    user = User.query.filter(User.username == "mergin").first()
    test_workspace = create_workspace()
    p = create_project("test_project", test_workspace, user)
    for i in range(10):
        user = add_user("test_user" + str(i), "ilovemergin")
        login(client, user.username, "ilovemergin")
        resp = client.post(
            f"/app/project/access-request/{test_workspace.name}/{p.name}",
            headers=json_headers,
        )
        assert resp.status_code == 200
    login(client, "mergin", "ilovemergin")
    resp = client.get(f"/app/project/access-request/{test_workspace.name}?page=1&per_page=5")
    assert resp.status_code == 200
    assert resp.json.get("count") == 10
    project_requests = resp.json.get("access_requests")
    assert len(project_requests) == 5
    resp = client.get(f"/app/project/access-request/{test_workspace.name}?page=2&per_page=5")
    project_requests = resp.json.get("access_requests")
    assert resp.status_code == 200
    assert len(project_requests) == 5
    #test order params
    resp = client.get(
        f"/app/project/access-request/{test_workspace.name}?page=1&per_page=15&order_params=expire DESC"
    )
    assert resp.json["access_requests"][0]["id"] == 10

def test_template_projects(client):
    u = add_user("TEMPLATES", "ilovemergin")
    test_workspace = create_workspace()
    p = create_project("my_template", test_workspace, u)
    resp = client.get(
        url_for("/app.mergin_sync_private_api_controller_template_projects")
    )
    assert resp.status_code == 200
    assert len(resp.json) == 1
    assert (
        resp.json[0]["name"] == p.name
        and resp.json[0]["namespace"] == test_workspace.name
    )


def test_update_project_access(client, diff_project):
    url = f"/app/project/{diff_project.id}/access"
    # create user and grant him write access
    user = add_user("reader", "reader")
    assert user.id not in diff_project.access.readers

    data = {"user_id": user.id, "role": "none"}
    # nothing happens
    resp = client.patch(url, headers=json_headers, data=json.dumps(data))
    assert resp.status_code == 200
    assert user.id not in diff_project.access.readers

    # grant read access
    data["role"] = "reader"
    resp = client.patch(url, headers=json_headers, data=json.dumps(data))
    assert resp.status_code == 200
    assert user.id in diff_project.access.readers

    # change to write access
    data["role"] = "writer"
    resp = client.patch(url, headers=json_headers, data=json.dumps(data))
    assert resp.status_code == 200
    assert user.id in diff_project.access.readers
    assert user.id in diff_project.access.writers

    # downgrade to read access
    data["role"] = "reader"
    resp = client.patch(url, headers=json_headers, data=json.dumps(data))
    assert resp.status_code == 200
    assert user.id in diff_project.access.readers
    assert user.id not in diff_project.access.writers

    # remove access
    data["role"] = "none"
    resp = client.patch(url, headers=json_headers, data=json.dumps(data))
    assert resp.status_code == 200
    assert user.id not in diff_project.access.readers
    assert user.id not in diff_project.access.writers

    # access of project creator can not be removed
    data["user_id"] = diff_project.creator_id
    resp = client.patch(
        f"/app/project/{diff_project.id}/access",
        headers=json_headers,
        data=json.dumps(data),
    )
    assert resp.status_code == 400

    # try to grant access to inaccessible user
    data = {"user_id": 100, "role": "reader"}
    # nothing happens
    resp = client.patch(url, headers=json_headers, data=json.dumps(data))
    assert resp.status_code == 404


def test_restore_project(client, diff_project):
    """Test delete project by user and restore by admin"""
    project_dir = diff_project.storage.project_dir
    client.delete(f"/v1/project/{diff_project.workspace.name}/{diff_project.name}")

    # tests listing
    resp = client.get("/app/admin/projects?page=1&per_page=10")
    assert resp.json["count"] == 1
    assert resp.json["projects"][0]["removed_at"]

    diff_project.workspace.active = True
    db.session.commit()
    resp = client.post(f"/app/project/removed-project/restore/{diff_project.id}")
    assert resp.status_code == 201

    assert not diff_project.removed_at
    assert not diff_project.removed_by
    assert os.path.exists(project_dir)


def test_admin_project_list(client):
    """Test paginate through all projects as a superuser"""
    user = User.query.filter_by(username="mergin").first()
    # there is already default project
    resp = client.get("/app/admin/projects?page=1&per_page=10")
    assert resp.status_code == 200
    assert resp.json.get("count") == 1
    # mark as inactive
    p = Project.query.get(resp.json["projects"][0]["id"])
    p.removed_at = datetime.datetime.utcnow()
    p.removed_by = user.username
    db.session.commit()

    # add more projects
    test_workspace = create_workspace()
    for i in range(14):
        create_project("foo" + str(i), test_workspace, user)

    resp = client.get("/app/admin/projects?page=1&per_page=10")
    assert resp.status_code == 200
    assert resp.json.get("count") == 15
    projects = resp.json.get("projects")
    assert len(projects) == 10
    assert "foo8" in projects[9]["name"]
    assert "v0" == projects[9]["version"]

    resp = client.get(
        "/app/admin/projects?page=1&per_page=10&order_params=removed_at ASC"
    )
    assert resp.status_code == 200
    assert resp.json["projects"][0]["name"] == p.name

    resp = client.get(
        "/app/admin/projects?page=1&per_page=15&order_params=created DESC"
    )
    assert resp.json["projects"][0]["name"] == "foo13"

    resp = client.get("/app/admin/projects?page=1&per_page=15&name=12")
    assert len(resp.json["projects"]) == 1
    assert resp.json["projects"][0]["name"] == "foo12"

    resp = client.get("/app/admin/projects?page=1&per_page=15&name=foo")
    assert len(resp.json["projects"]) == 14

    resp = client.get("/app/admin/projects?page=1&per_page=15&workspace=invalid")
    assert len(resp.json["projects"]) == 0

    resp = client.get("/app/admin/projects?page=1&per_page=15&workspace=mergin")
    assert len(resp.json["projects"]) == 15