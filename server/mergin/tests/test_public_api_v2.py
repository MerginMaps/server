# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial
from datetime import datetime

from . import DEFAULT_USER
from .utils import (
    add_user,
    login,
    login_as_admin,
    create_workspace,
    create_project,
    upload_file_to_project,
)
from ..app import db
from mergin.sync.models import Project
from tests import test_project, test_workspace_id

from ..auth.models import User
from ..config import Configuration
from ..sync.models import ProjectRole


def test_schedule_delete_project(client):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    response = client.post(f"v2/projects/{project.id}/scheduleDelete")
    assert response.status_code == 204
    updated = Project.query.get(project.id)
    assert updated.removed_at and updated.removed_by
    assert updated.storage_params
    response = client.post(f"v2/projects/{project.id}/scheduleDelete")
    assert response.status_code == 404


def test_delete_project_now(client):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    original_creator_id = project.creator_id
    response = client.delete(f"v2/projects/{project.id}")
    assert response.status_code == 204
    db.session.rollback()
    assert project.creator_id == original_creator_id
    project = Project.query.get(project.id)
    assert project.removed_at and not project.storage_params and not project.files
    response = client.delete(f"v2/projects/{project.id}")
    assert response.status_code == 404


def test_delete_after_schedule(client):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    response = client.post(f"v2/projects/{project.id}/scheduleDelete")
    assert response.status_code == 204
    response = client.delete(f"v2/projects/{project.id}")
    assert response.status_code == 204


def test_rename_project(client):
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    data = {"name": "new_project_name"}
    response = client.patch(f"v2/projects/{project.id}", json=data)
    assert response.status_code == 204
    assert project.name == "new_project_name"
    # name already exists
    response = client.patch(f"v2/projects/{project.id}", json=data)
    assert response.status_code == 409
    # invalid project name
    response = client.patch(f"v2/projects/{project.id}", json={"name": ".new_name"})
    assert response.status_code == 400
    assert response.json["code"] == "InvalidProjectName"
    response = client.patch(
        f"v2/projects/{project.id}", json={"name": ".new_project_name"}
    )
    assert response.status_code == 400
    assert response.json["code"] == "InvalidProjectName"


def test_project_members(client):
    """Test CRUD endpoints for direct project members"""
    project = Project.query.filter_by(
        workspace_id=test_workspace_id, name=test_project
    ).first()
    url = f"v2/projects/{project.id}/collaborators"
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json) == 1

    user = add_user("user", "password")
    # user not a member yet
    response = client.delete(url + f"/{user.id}")
    assert response.status_code == 404

    role = ProjectRole.READER.value
    response = client.patch(url + f"/{user.id}", json={"role": role})
    assert response.status_code == 404

    # add direct access
    response = client.post(url, json={"role": role, "user": user.email})
    assert response.status_code == 201
    assert response.json["id"] == user.id
    assert response.json["project_role"] == role

    Configuration.GLOBAL_READ = 0
    Configuration.GLOBAL_WRITE = 0
    Configuration.GLOBAL_ADMIN = 0
    response = client.get(url)
    assert len(response.json) == 2
    member = next(u for u in response.json if u["id"] == user.id)
    assert member["project_role"] == role
    assert member["workspace_role"] == "guest"

    response = client.patch(
        url + f"/{user.id}", json={"role": ProjectRole.WRITER.value}
    )
    assert response.status_code == 200
    assert response.json["project_role"] == ProjectRole.WRITER.value

    response = client.delete(url + f"/{user.id}")
    assert response.status_code == 204

    response = client.get(url)
    assert len(response.json) == 1

    # test access only by workspace role
    Configuration.GLOBAL_READ = 1
    response = client.get(url)
    member = next(u for u in response.json if u["id"] == user.id)
    assert not member["project_role"]
    assert member["workspace_role"] == "reader"

    # access provided by workspace role cannot be removed directly
    response = client.delete(url + f"/{user.id}")
    assert response.status_code == 404


def test_get_project(client):
    """Test get project info endpoint"""
    admin = User.query.filter_by(username=DEFAULT_USER[0]).first()
    test_workspace = create_workspace()
    project = create_project("new_project", test_workspace, admin)
    add_user("test_user", "ilovemergin")
    login(client, "test_user", "ilovemergin")
    # lack of permissions
    response = client.get(f"v2/projects/{project.id}")
    assert response.status_code == 403
    # access public project
    project.public = True
    db.session.commit()
    response = client.get(f"v2/projects/{project.id}")
    assert response.status_code == 200
    assert response.json["public"] is True
    # project scheduled for deletion
    login_as_admin(client)
    project.public = False
    project.removed_at = datetime.utcnow()
    db.session.commit()
    response = client.get(f"v2/projects/{project.id}")
    assert response.status_code == 404
    # success
    project.removed_at = None
    db.session.commit()
    response = client.get(f"v2/projects/{project.id}")
    assert response.status_code == 200
    expected_keys = {
        "id",
        "name",
        "workspace",
        "role",
        "version",
        "created_at",
        "updated_at",
        "public",
        "size",
    }
    assert expected_keys == response.json.keys()
    # create new versions
    files = ["test.txt", "test3.txt", "test.qgs"]
    for file in files:
        upload_file_to_project(project, file, client)
    # project version does not exist
    response = client.get(
        f"v2/projects/{project.id}?files_at_version=v{project.latest_version+1}"
    )
    assert response.status_code == 404
    # files
    response = client.get(
        f"v2/projects/{project.id}?files_at_version=v{project.latest_version-2}"
    )
    assert response.status_code == 200
    assert len(response.json["files"]) == 1
    assert any(resp_files["path"] == files[0] for resp_files in response.json["files"])
    assert not any(
        resp_files["path"] == files[1] for resp_files in response.json["files"]
    )
    response = client.get(
        f"v2/projects/{project.id}?files_at_version=v{project.latest_version}"
    )
    assert len(response.json["files"]) == 3
    assert {f["path"] for f in response.json["files"]} == set(files)
